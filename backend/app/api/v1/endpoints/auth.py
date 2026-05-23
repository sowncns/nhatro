from typing import List
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.services.auth_service import AuthService
from app.services.otp_service import OTPService
from app.services.session_service import SessionService
from app.schemas.schemas import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshTokenRequest, ForgotPasswordRequest, ResetPasswordRequest,
    ChangePasswordRequest, UserSessionResponse, RegisterOTPSendRequest,
)
from app.core.deps import get_current_user
from app.models.models import User
from app.core.security import verify_password

router = APIRouter()


@router.post("/register/send-otp")
async def send_register_otp(data: RegisterOTPSendRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    otp_service = OTPService(db)
    otp_code = await otp_service.create_otp(email=data.email)
    try:
        await otp_service.send_email_otp(data.email, otp_code)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Không gửi được mã OTP: {str(exc)}") from exc

    return {"message": "OTP sent successfully"}


@router.post("/register", response_model=TokenResponse)
async def register(
    data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None

    return await service.register(
        data,
        user_agent=user_agent,
        ip_address=ip_address,
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
  
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")

    # 2. Call SessionService to enforce limits, create session and tokens
    service = SessionService(db)
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    
    return await service.create_session(
        user_id=user.id,
        device_id=data.device_id,
        device_name=data.device_name,
        user_agent=user_agent,
        ip_address=ip_address,
        policy=data.policy.value,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    service = SessionService(db)
    return await service.refresh_session(data.refresh_token)


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = auth_header.split(" ")[1]
    
    from app.core.security import verify_token
    payload = verify_token(token, "access")
    if not payload or not payload.get("sid"):
        raise HTTPException(status_code=401, detail="Invalid token")
        
    service = SessionService(db)
    await service.revoke_session(payload.get("sid"), current_user.id)
    return {"message": "Logged out successfully"}


@router.post("/logout-all")
async def logout_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SessionService(db)
    await service.revoke_all_sessions(current_user.id)
    return {"message": "All sessions revoked successfully"}


@router.get("/sessions", response_model=List[UserSessionResponse])
async def get_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.repositories.user_session import UserSessionRepository
    repo = UserSessionRepository(db)
    return await repo.get_active_sessions_by_user_id(current_user.id)


@router.delete("/sessions/{id}")
async def delete_session(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SessionService(db)
    await service.revoke_session(id, current_user.id)
    return {"message": f"Session {id} revoked successfully"}


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    msg = await service.forgot_password(data.email)
    return {"message": msg}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    await service.reset_password(data.token, data.new_password)
    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.change_password(current_user, data.current_password, data.new_password)
    return {"message": "Password changed successfully"}


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "avatar_url": current_user.avatar_url,
        "role": current_user.role,
    }
