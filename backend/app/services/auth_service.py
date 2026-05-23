"""Authentication Service"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from slugify import slugify

from app.models.models import User, Organization, RefreshToken, OrganizationMember, OrgMemberRole
from app.core.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, verify_token, create_password_reset_token,
    verify_password_reset_token
)
from app.core.config import settings
from app.schemas.schemas import RegisterRequest, LoginRequest, TokenResponse
from app.services.otp_service import OTPService


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(
        self,
        data: RegisterRequest,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> TokenResponse:
        # Check email exists
        existing = await self.db.execute(select(User).where(User.email == data.email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

        otp_service = OTPService(self.db)
        is_valid_otp = await otp_service.verify_otp(email=data.email, otp_code=data.otp_code)
        if not is_valid_otp:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP code")

        # Create user
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            phone=data.phone,
            role="owner",
            is_verified=True,  # Auto-verify for now
        )
        self.db.add(user)
        await self.db.flush()

        # Create organization
        org_name = data.organization_name
        if not org_name or not org_name.strip():
            org_name = f"Nhà trọ {data.full_name}"

        slug = slugify(org_name)
        # Ensure unique slug
        slug_count = await self.db.execute(
            select(Organization).where(Organization.slug.like(f"{slug}%"))
        )
        count = len(slug_count.scalars().all())
        if count > 0:
            slug = f"{slug}-{count}"

        org = Organization(
            name=org_name,
            slug=slug,
            owner_id=user.id,
            subscription_plan="free",
        )
        self.db.add(org)
        await self.db.flush()

        # Add user as owner member
        member = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role=OrgMemberRole.OWNER,
        )
        self.db.add(member)
        await self.db.flush()

        from app.services.session_service import SessionService
        session_service = SessionService(self.db)
        return await session_service.create_session(
            user_id=user.id,
            device_id=None,
            device_name="Thiết bị đăng ký mới",
            user_agent=user_agent,
            ip_address=ip_address,
        )

    async def login(self, data: LoginRequest) -> TokenResponse:
        result = await self.db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(status_code=400, detail="Account is deactivated")

        return await self._create_tokens(user)

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        payload = verify_token(refresh_token, "refresh")
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Check token in DB
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token == refresh_token,
                RefreshToken.is_revoked == False,
            )
        )
        token_obj = result.scalar_one_or_none()
        if not token_obj:
            raise HTTPException(status_code=401, detail="Refresh token revoked or not found")

        if token_obj.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Refresh token expired")

        # Revoke old token
        token_obj.is_revoked = True
        await self.db.flush()

        # Get user
        result = await self.db.execute(select(User).where(User.id == payload.get("sub")))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return await self._create_tokens(user)

    async def _create_tokens(self, user: User) -> TokenResponse:
        from app.schemas.schemas import UserResponse

        access_token = create_access_token({"sub": user.id})
        refresh_token = create_refresh_token({"sub": user.id})

        # Store refresh token
        token_obj = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(token_obj)
        await self.db.flush()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user),
        )

    async def forgot_password(self, email: str) -> str:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            # Don't reveal if email exists
            return "If the email exists, a reset link has been sent"

        token = create_password_reset_token(email)
        # TODO: send email
        return "Reset email sent"

    async def reset_password(self, token: str, new_password: str) -> bool:
        email = verify_password_reset_token(token)
        if not email:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.hashed_password = hash_password(new_password)
        await self.db.flush()
        return True

    async def change_password(self, user: User, current_password: str, new_password: str) -> bool:
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        if verify_password(new_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password",
            )

        user.hashed_password = hash_password(new_password)
        await self.db.execute(
            RefreshToken.__table__.update()
            .where(RefreshToken.user_id == user.id)
            .values(is_revoked=True)
        )
        await self.db.flush()
        return True
