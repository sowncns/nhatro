"""Maintenance Endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.models.models import MaintenanceRequest
from app.schemas.schemas import MaintenanceCreate, MaintenanceUpdate, MaintenanceResponse, PaginatedResponse
from app.repositories.base import BaseRepository

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_maintenance(
    page: int = Query(1, ge=1),
    size: int = Query(20),
    status: str = None,
    priority: str = None,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(MaintenanceRequest, db, ctx.organization_id)
    filters = []
    if status:
        filters.append(MaintenanceRequest.status == status)
    if priority:
        filters.append(MaintenanceRequest.priority == priority)
    total = await repo.count(filters)
    items = await repo.get_all(skip=(page - 1) * size, limit=size, filters=filters,
                                order_by=MaintenanceRequest.created_at.desc())
    return PaginatedResponse(
        items=[MaintenanceResponse.model_validate(r) for r in items],
        total=total, page=page, size=size,
        pages=(total + size - 1) // size,
    )


@router.post("", response_model=MaintenanceResponse, status_code=201)
async def create_maintenance(
    data: MaintenanceCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(MaintenanceRequest, db, ctx.organization_id)
    req = await repo.create(data.model_dump())
    return MaintenanceResponse.model_validate(req)


@router.patch("/{req_id}", response_model=MaintenanceResponse)
async def update_maintenance(
    req_id: str,
    data: MaintenanceUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone
    repo = BaseRepository(MaintenanceRequest, db, ctx.organization_id)
    update_data = data.model_dump(exclude_none=True)
    if update_data.get("status") == "resolved":
        update_data["resolved_at"] = datetime.now(timezone.utc)
    req = await repo.update(req_id, update_data)
    if not req:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")
    return MaintenanceResponse.model_validate(req)
