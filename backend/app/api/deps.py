from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.core.security import verify_token
from app.database.session import get_db
from app.models.models import User, Organization, OrganizationMember

security = HTTPBearer()


async def get_current_user(
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
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
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


def require_owner_or_manager(ctx: TenantContext = Depends(get_tenant_context)):
    """Only owner and managers can modify resources"""
    if ctx.user.role not in ["owner", "manager"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return ctx
