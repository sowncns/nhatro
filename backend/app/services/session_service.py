import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.models import User, Organization, SubscriptionPlan
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.core.config import settings
from app.core.subscription import SubscriptionLimits
from app.utils.redis_helper import RedisSessionHelper
from app.utils.lock_helper import RedisDistributedLock
from app.repositories.user_session import UserSessionRepository
from app.schemas.schemas import TokenResponse, UserResponse

logger = logging.getLogger("app.session_service")


class SessionService:
    """Service to handle user session lifecycle, subscription limits, and security."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserSessionRepository(db)

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash a token using SHA-256 for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    async def _get_user_device_limit(self, user: User) -> int:
        """Determine device limit based on user's active organization subscription."""
        # Query the organization owned by this user
        result = await self.db.execute(
            select(Organization).where(
                Organization.owner_id == user.id,
                Organization.is_active == True
            )
        )
        org = result.scalar_one_or_none()
        if not org:
           
            return SubscriptionLimits.get_limits(SubscriptionPlan.FREE)["max_devices"]

        limits = SubscriptionLimits.get_limits(org.subscription_plan)
        return limits.get("max_devices", 1)

    async def create_session(
        self,
        user_id: str,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        policy: str = "revoke_oldest_session",
    ) -> TokenResponse:
        """Create a new session for a user, enforcing subscription limits with lock protection."""
        if not device_id:
            # Generate a reliable device fingerprint from user_agent and ip_address
            fingerprint = f"{user_agent or ''}_{ip_address or ''}"
            device_id = f"gen_{hashlib.md5(fingerprint.encode()).hexdigest()}"
            if not device_name:
                device_name = "Unknown Web Device"

        lock_key = f"lock:user:{user_id}"

        # 1. Acquire Distributed Lock to prevent race conditions
        async with RedisDistributedLock(lock_key, expire_seconds=10, acquire_timeout=5.0):
            # 2. Lock user row in DB to ensure transactional consistency
            user_result = await self.db.execute(
                select(User).where(User.id == user_id).with_for_update()
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            if not user.is_active:
                raise HTTPException(status_code=400, detail="User account is deactivated")

            # 3. Get subscription limit
            max_devices = await self._get_user_device_limit(user)
            active_count = await self.repo.count_active_sessions(user_id)

            # 4. Handle session limit overflow policies
            if active_count >= max_devices:
                if policy == "reject_new_login":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Đã đạt giới hạn đăng nhập {max_devices} thiết bị của gói dịch vụ. Vui lòng đăng xuất thiết bị khác.",
                    )
                elif policy == "revoke_oldest_session":
                    # Revoke the oldest active session
                    await self.repo.revoke_oldest_session(user_id)
                elif policy == "revoke_all_old_sessions":
                    # Revoke all current active sessions
                    await self.revoke_all_sessions(user_id)

            # 5. Generate tokens embedded with Session ID (sid)
            from app.database.models import gen_uuid
            session_id = gen_uuid()

            access_token = create_access_token({"sub": user_id, "sid": session_id})
            refresh_token = create_refresh_token({"sub": user_id, "sid": session_id})
            refresh_token_hash = self._hash_token(refresh_token)

            # Expires at matches refresh token expiration
            expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

            # 6. Save to DB
            session_obj = await self.repo.create_session(
                user_id=user_id,
                refresh_token_hash=refresh_token_hash,
                device_id=device_id,
                device_name=device_name,
                user_agent=user_agent,
                ip_address=ip_address,
                expires_at=expires_at,
                session_id=session_id,
            )

            # 7. Cache in Redis
            session_data = {
                "id": session_id,
                "user_id": user_id,
                "device_id": device_id,
                "device_name": device_name,
                "is_active": True,
                "expires_at": expires_at.isoformat(),
            }
            ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
            await RedisSessionHelper.cache_session(session_id, session_data, ttl)
            await RedisSessionHelper.add_user_session_to_list(user_id, session_id)

            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                user=UserResponse.model_validate(user),
                device_id=device_id,
            )

    async def refresh_session(self, refresh_token: str) -> TokenResponse:
        """Rotate and refresh both access and refresh tokens, protecting against reuse attacks."""
        payload = verify_token(refresh_token, "refresh")
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user_id = payload.get("sub")
        session_id = payload.get("sid")

        if not session_id:
            raise HTTPException(
                status_code=401,
                detail="Legacy refresh token format. Please log in again.",
            )

        # 1. Retrieve session
        session = await self.repo.get_session(session_id)
        if not session or not session.is_active:
            raise HTTPException(status_code=401, detail="Session is inactive or logged out")

        if session.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            # Expired session
            session.is_active = False
            await self.db.flush()
            await RedisSessionHelper.revoke_cached_session(session_id, user_id)
            raise HTTPException(status_code=401, detail="Session has expired")

        # 2. Token Reuse Detection
        current_hash = self._hash_token(refresh_token)
        if session.refresh_token_hash != current_hash:
            # CRITICAL SECURITY ALERT: Token reuse detected!
            # Revoke all sessions of this user immediately to protect the account
            logger.warning(
                f"SECURITY WARNING: Refresh token reuse detected for user {user_id} on session {session_id}! Revoking all sessions."
            )
            await self.revoke_all_sessions(user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cảnh báo bảo mật: Phiên đăng nhập đã bị thu hồi do phát hiện token được sử dụng lại.",
            )

        # 3. Rotate tokens (generate new access and refresh token)
        new_access_token = create_access_token({"sub": user_id, "sid": session_id})
        new_refresh_token = create_refresh_token({"sub": user_id, "sid": session_id})
        new_hash = self._hash_token(new_refresh_token)

        # 4. Update session DB
        session.refresh_token_hash = new_hash
        session.last_seen = datetime.now(timezone.utc)
        await self.db.flush()

        # 5. Update Redis Cache
        session_data = {
            "id": session_id,
            "user_id": user_id,
            "device_id": session.device_id,
            "device_name": session.device_name,
            "is_active": True,
            "expires_at": session.expires_at.isoformat(),
        }
        ttl = int((session.expires_at.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).total_seconds())
        if ttl > 0:
            await RedisSessionHelper.cache_session(session_id, session_data, ttl)

        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one()

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            user=UserResponse.model_validate(user),
            device_id=session.device_id,
        )

    async def revoke_session(self, session_id: str, user_id: str) -> bool:
        """Revoke a specific session."""
        session = await self.repo.get_session(session_id)
        if not session or session.user_id != user_id:
            raise HTTPException(status_code=404, detail="Session not found or unauthorized")

        success = await self.repo.revoke_session(session_id)
        if success:
            await RedisSessionHelper.revoke_cached_session(session_id, user_id)
        return success

    async def revoke_all_sessions(self, user_id: str, except_session_id: Optional[str] = None) -> int:
        """Revoke all active sessions of a user."""
        count = await self.repo.revoke_all_sessions(user_id, except_session_id)
        if except_session_id:
            # Revoke all but one from cache
            active_sids = await RedisSessionHelper.get_user_sessions_list(user_id)
            for sid in active_sids:
                if sid != except_session_id:
                    await RedisSessionHelper.revoke_cached_session(sid, user_id)
        else:
            # Revoke all from cache
            await RedisSessionHelper.revoke_all_user_sessions_cached(user_id)
        return count
