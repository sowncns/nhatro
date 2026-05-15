"""Maintenance Endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.database.models import MaintenanceRequest
from app.schemas.schemas import MaintenanceCreate, MaintenanceUpdate, MaintenanceResponse, PaginatedResponse
from app.repositories.base import BaseRepository

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_maintenance(
    page: int = Query(1, ge=1),
    size: int = Query(20),
    mode: str = Query("active"),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(MaintenanceRequest, db, ctx.organization_id)
    total = await repo.count(mode=mode)
    items = await repo.get_all(skip=(page - 1) * size, limit=size, mode=mode, order_by=MaintenanceRequest.created_at.desc())
    return PaginatedResponse(
        items=[MaintenanceResponse.model_validate(m) for m in items],
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


@router.patch("/{request_id}", response_model=MaintenanceResponse)
async def update_maintenance(
    request_id: str,
    data: MaintenanceUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(MaintenanceRequest, db, ctx.organization_id)
    req = await repo.update(request_id, data.model_dump(exclude_none=True))
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    return MaintenanceResponse.model_validate(req)
