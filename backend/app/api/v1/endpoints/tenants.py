"""Tenants Endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.models.models import Tenant
from app.schemas.schemas import TenantCreate, TenantUpdate, TenantResponse, PaginatedResponse
from app.repositories.base import BaseRepository
from app.services.cache_service import CacheService
from app.services.invalidate_helper import InvalidateHelper
from app.core.cache_constants import TTL_TENANT_LIST, TTL_TENANT_DETAIL

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_tenants(
    page: int = Query(1, ge=1),
    size: int = Query(20),
    search: Optional[str] = None,
    mode: str = Query("active"),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"tenants:list:{ctx.organization_id}:{page}:{size}:{search}:{mode}"
    cached = await CacheService.get(cache_key)
    if cached:
        return cached

    repo = BaseRepository(Tenant, db, ctx.organization_id)
    filters = []
    if search:
        from sqlalchemy import or_
        filters.append(or_(
            Tenant.full_name.ilike(f"%{search}%"),
            Tenant.phone.ilike(f"%{search}%"),
        ))
    total = await repo.count(filters, mode=mode)
    items = await repo.get_all(skip=(page - 1) * size, limit=size, filters=filters, mode=mode)
    res = PaginatedResponse(
        items=[TenantResponse.model_validate(t) for t in items],
        total=total, page=page, size=size,
        pages=(total + size - 1) // size,
    )
    await CacheService.set(cache_key, res.model_dump(), expire=TTL_TENANT_LIST)
    return res


@router.post("", response_model=TenantResponse, status_code=201)
async def create_tenant(
    data: TenantCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(Tenant, db, ctx.organization_id)
    if data.id_card:
        existing = await repo.get_all(filters=[Tenant.id_card == data.id_card, Tenant.is_active == True])
        if existing:
            raise HTTPException(status_code=400, detail="Khách thuê với số CCCD này đã tồn tại trong hệ thống")
            
    tenant = await repo.create(data.model_dump())
    await InvalidateHelper.invalidate_tenant(ctx.organization_id)
    return TenantResponse.model_validate(tenant)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"tenants:detail:{ctx.organization_id}:{tenant_id}"
    cached = await CacheService.get(cache_key)
    if cached:
        return cached

    repo = BaseRepository(Tenant, db, ctx.organization_id)
    tenant = await repo.get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    res = TenantResponse.model_validate(tenant)
    await CacheService.set(cache_key, res.model_dump(), expire=TTL_TENANT_DETAIL)
    return res


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
        raise HTTPException(status_code=404, detail="Not found")
    await InvalidateHelper.invalidate_tenant(ctx.organization_id, tenant_id)
    return TenantResponse.model_validate(tenant)
