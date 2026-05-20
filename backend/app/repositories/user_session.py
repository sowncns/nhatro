from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_
from app.database.models import UserSession


class UserSessionRepository:
    """Repository for managing UserSession database operations.

    This repository is platform-wide (does not apply organization_id tenant isolation
    since user sessions are global to the User, not a specific organization).
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get a session by its ID."""
        result = await self.db.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_active_sessions_by_user_id(self, user_id: str) -> List[UserSession]:
        """Get all active sessions for a user, ordered by last_seen descending."""
        result = await self.db.execute(
            select(UserSession)
            .where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.now(timezone.utc),
                )
            )
            .order_by(UserSession.last_seen.desc())
        )
        return list(result.scalars().all())

    async def count_active_sessions(self, user_id: str) -> int:
        """Count active, unexpired sessions for a user."""
        result = await self.db.execute(
            select(func.count(UserSession.id)).where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.now(timezone.utc),
                )
            )
        )
        return result.scalar_one() or 0

    async def create_session(
        self,
        user_id: str,
        refresh_token_hash: str,
        device_id: str,
        device_name: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> UserSession:
        """Create a new user session in the database."""
        if not expires_at:
            # Fallback to default 7 days if not provided
            from app.core.config import settings
            from datetime import timedelta
            expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        session = UserSession(
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            device_id=device_id,
            device_name=device_name,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
            is_active=True,
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_session_by_hash(self, refresh_token_hash: str) -> Optional[UserSession]:
        """Find a session by its refresh token hash."""
        result = await self.db.execute(
            select(UserSession).where(UserSession.refresh_token_hash == refresh_token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_session(self, session_id: str) -> bool:
        """Mark a session as inactive."""
        result = await self.db.execute(
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(is_active=False)
        )
        await self.db.flush()
        return result.rowcount > 0

    async def revoke_oldest_session(self, user_id: str) -> bool:
        """Revoke the oldest active session for a user (by last_seen)."""
        active_sessions = await self.get_active_sessions_by_user_id(user_id)
        if not active_sessions:
            return False
            
        # The list is sorted by last_seen DESC, so the last element is the oldest
        oldest_session = active_sessions[-1]
        oldest_session.is_active = False
        await self.db.flush()
        
        # Revoke from Redis cache as well
        from app.utils.redis_helper import RedisSessionHelper
        await RedisSessionHelper.revoke_cached_session(oldest_session.id, user_id)
        return True

    async def revoke_all_sessions(
        self, user_id: str, except_session_id: Optional[str] = None
    ) -> int:
        """Revoke all sessions for a user, with option to keep one active."""
        filters = [UserSession.user_id == user_id, UserSession.is_active == True]
        if except_session_id:
            filters.append(UserSession.id != except_session_id)

        result = await self.db.execute(
            update(UserSession)
            .where(and_(*filters))
            .values(is_active=False)
        )
        await self.db.flush()
        return result.rowcount

    async def update_last_seen(self, session_id: str, ip_address: Optional[str] = None) -> None:
        """Update last_seen timestamp and optionally IP address."""
        values = {"last_seen": datetime.now(timezone.utc)}
        if ip_address:
            values["ip_address"] = ip_address

        await self.db.execute(
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(**values)
        )
        await self.db.flush()
