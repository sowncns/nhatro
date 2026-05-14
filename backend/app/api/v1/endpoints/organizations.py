"""Organizations Endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.schemas.schemas import OrganizationResponse, OrganizationUpdate
from app.models.models import Organization
from app.repositories.base import BaseRepository

router = APIRouter()


@router.get("/me", response_model=OrganizationResponse)
async def get_my_organization(
    ctx: TenantContext = Depends(get_tenant_context),
):
    return OrganizationResponse.model_validate(ctx.organization)


@router.patch("/me", response_model=OrganizationResponse)
async def update_organization(
    data: OrganizationUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import update
    await db.execute(
        update(Organization)
        .where(Organization.id == ctx.organization_id)
        .values(**data.model_dump(exclude_none=True))
    )
    await db.flush()
    await db.refresh(ctx.organization)
    return OrganizationResponse.model_validate(ctx.organization)
