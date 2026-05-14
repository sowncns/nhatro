"""Dashboard Endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/stats")
async def get_stats(
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db, ctx.organization_id)
    return await service.get_stats()


@router.get("/revenue")
async def get_revenue(
    year: int = Query(default=None),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    if not year:
        year = datetime.now().year
    service = DashboardService(db, ctx.organization_id)
    return await service.get_monthly_revenue(year)


@router.get("/occupancy")
async def get_occupancy(
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db, ctx.organization_id)
    return await service.get_room_occupancy_trend()
