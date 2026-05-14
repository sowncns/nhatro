"""Tenants Endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.models.models import Tenant, Contract, MeterReading
from app.schemas.schemas import (
    TenantCreate, TenantUpdate, TenantResponse,
    ContractCreate, ContractResponse,
    MeterReadingCreate, MeterReadingResponse,
    PaginatedResponse
)
from app.repositories.base import BaseRepository
import uuid

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_tenants(
    page: int = Query(1, ge=1),
    size: int = Query(20),
    search: Optional[str] = None,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(Tenant, db, ctx.organization_id)
    filters = [Tenant.is_active == True]
    if search:
        from sqlalchemy import or_
        filters.append(or_(
            Tenant.full_name.ilike(f"%{search}%"),
            Tenant.phone.ilike(f"%{search}%"),
        ))
    total = await repo.count(filters)
    items = await repo.get_all(skip=(page - 1) * size, limit=size, filters=filters)
    return PaginatedResponse(
        items=[TenantResponse.model_validate(t) for t in items],
        total=total, page=page, size=size,
        pages=(total + size - 1) // size,
    )


@router.post("", response_model=TenantResponse, status_code=201)
async def create_tenant(
    data: TenantCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(Tenant, db, ctx.organization_id)
    tenant = await repo.create(data.model_dump())
    return TenantResponse.model_validate(tenant)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(Tenant, db, ctx.organization_id)
    tenant = await repo.get(tenant_id)
    if not tenant:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Tenant not found")
    return TenantResponse.model_validate(tenant)


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    data: TenantUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(Tenant, db, ctx.organization_id)
    tenant = await repo.update(tenant_id, data.model_dump(exclude_none=True))
    if not tenant:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")
    return TenantResponse.model_validate(tenant)
