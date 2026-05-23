from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.core.security import verify_token
from app.database.session import get_db, AsyncSessionLocal
from app.models.models import User, Organization, OrganizationMember, UserRole
from app.utils.redis_helper import RedisSessionHelper

security = HTTPBearer()


async def update_session_last_seen_task(session_id: str, ip_address: Optional[str]):
    """Background task to update last_seen timestamp in the DB without blocking the request."""
    try:
        async with AsyncSessionLocal() as local_db:
            from app.repositories.user_session import UserSessionRepository
            repo = UserSessionRepository(local_db)
            await repo.update_last_seen(session_id, ip_address)
            await local_db.commit()
    except Exception as e:
        import logging
        logging.getLogger("app.deps").error(f"Error in background task update_session_last_seen: {e}")


async def get_current_user(
    request: Request,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = verify_token(token, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    session_id = payload.get("sid")

    # 1. Require sid (Session ID) for session limit checks
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Legacy token format. Please log in again.",
        )

    # 2. Check session active in Redis
    cached = await RedisSessionHelper.get_cached_session(session_id)
    is_active = False
    
    if cached:
        is_active = cached.get("is_active", False)
    else:
        # Fallback to DB
        from app.repositories.user_session import UserSessionRepository
        repo = UserSessionRepository(db)
        session_db = await repo.get_session(session_id)
        
        if (
            session_db 
            and session_db.is_active 
            and session_db.expires_at.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc)
        ):
            is_active = True
            # Cache back to Redis
            ttl = int((session_db.expires_at.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).total_seconds())
            if ttl > 0:
                session_data = {
                    "id": str(session_db.id),
                    "user_id": str(session_db.user_id),
                    "device_id": session_db.device_id,
                    "device_name": session_db.device_name,
                    "is_active": True,
                    "expires_at": session_db.expires_at.isoformat(),
                }
                await RedisSessionHelper.cache_session(session_id, session_data, ttl)
                await RedisSessionHelper.add_user_session_to_list(str(session_db.user_id), session_id)

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked or expired. Please log in again.",
        )

    # 3. Fetch user
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # 4. Asynchronously update session's last_seen
    client_ip = request.client.host if request.client else None
    background_tasks.add_task(update_session_last_seen_task, session_id, client_ip)

    return user


async def get_current_organization(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    """Get the organization for the current user (owner or member)"""
    # Check if user owns an organization
    result = await db.execute(
        select(Organization).where(
            Organization.owner_id == current_user.id,
            Organization.is_active == True,
        )
    )
    org = result.scalar_one_or_none()
    if org:
        return org

    # Check if user is a member
    result = await db.execute(
        select(Organization)
        .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
        .where(
            OrganizationMember.user_id == current_user.id,
            Organization.is_active == True,
        )
    )
    org = result.scalar_one_or_none()
    if org:
        return org

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No organization found for this user",
    )


class TenantContext:
    """Dependency that provides user + organization context for tenant isolation"""
    def __init__(self, user: User, organization: Organization):
        self.user = user
        self.organization = organization
        self.organization_id = organization.id


async def get_tenant_context(
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
) -> TenantContext:
    return TenantContext(user=user, organization=org)


class PortalTenantContext:
    def __init__(self, tenant_id: str, contract_ids: list[str]):
        self.tenant_id = tenant_id
        self.contract_ids = contract_ids


async def get_portal_tenant_context(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> PortalTenantContext:
    token = credentials.credentials
    payload = verify_token(token, "access")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
        
    role = payload.get("role")
    if role != "tenant":
        raise HTTPException(status_code=403, detail="Forbidden: Not a tenant")
        
    tenant_id = payload.get("sub")
    
    # Fetch active contracts for this tenant
    from app.database.models import Contract
    from sqlalchemy import select
    result = await db.execute(
        select(Contract).where(
            Contract.tenant_id == tenant_id,
            Contract.status == "ACTIVE"
        )
    )
    contracts = result.scalars().all()
    contract_ids = [str(c.id) for c in contracts]
    
    return PortalTenantContext(tenant_id=tenant_id, contract_ids=contract_ids)


def require_owner_or_manager(ctx: TenantContext = Depends(get_tenant_context)):
    """Only owner and managers can modify resources"""
    if ctx.user.role not in [UserRole.OWNER, UserRole.MANAGER, "owner", "manager"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return ctx


def require_owner(ctx: TenantContext = Depends(get_tenant_context)):
    """Only the paying landlord/owner can change SaaS billing."""
    if ctx.user.role not in [UserRole.OWNER, "owner"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can manage billing")
    return ctx


def require_platform_admin(current_user: User = Depends(get_current_user)) -> User:
    """Only platform admins can manage SaaS customers and payments."""
    if current_user.role not in [UserRole.PLATFORM_ADMIN, "platform_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform admin only")
    return current_user
