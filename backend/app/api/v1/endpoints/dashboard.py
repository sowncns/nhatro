"""Dashboard Endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.services.dashboard_service import DashboardService
from app.services.cache_service import CacheService

router = APIRouter()


@router.get("/stats")
async def get_stats(
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"dashboard:stats:{ctx.organization_id}"
    cached = await CacheService.get(cache_key)
    if cached:
        return cached

    service = DashboardService(db, ctx.organization_id)
    result = await service.get_stats()
    await CacheService.set(cache_key, result.model_dump(), expire=300)
    return result


@router.get("/revenue")
async def get_revenue(
    year: int = Query(default=None),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    if not year:
        year = datetime.now().year

    cache_key = f"dashboard:rev:{ctx.organization_id}:{year}"
    cached = await CacheService.get(cache_key)
    if cached:
        return cached

    service = DashboardService(db, ctx.organization_id)
    result = await service.get_monthly_revenue(year)
    await CacheService.set(cache_key, result, expire=300)
    return result


@router.get("/occupancy")
async def get_occupancy(
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"dashboard:occ:{ctx.organization_id}"
    cached = await CacheService.get(cache_key)
    if cached:
        return cached

    service = DashboardService(db, ctx.organization_id)
    result = await service.get_room_occupancy_trend()
    await CacheService.set(cache_key, result, expire=300)
    return result

@router.get("/search")
async def global_search(
    q: str = Query(..., min_length=1),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    from app.models.models import Tenant, Room, Invoice, BoardingHouse
    from sqlalchemy import select, or_

    results = []
    
    # Search Tenants
    tenant_stmt = select(Tenant).filter(
        Tenant.organization_id == ctx.organization_id,
        Tenant.is_active == True,
        Tenant.archived_at == None,
        or_(Tenant.full_name.ilike(f"%{q}%"), Tenant.phone.ilike(f"%{q}%"))
    ).limit(5)
    tenants = (await db.execute(tenant_stmt)).scalars().all()
    for t in tenants:
        results.append({
            "id": str(t.id),
            "type": "tenant",
            "title": t.full_name,
            "subtitle": t.phone,
            "link": f"/tenants"
        })

    # Search Rooms
    room_stmt = select(Room, BoardingHouse).join(BoardingHouse, Room.boarding_house_id == BoardingHouse.id).filter(
        Room.organization_id == ctx.organization_id,
        Room.room_number.ilike(f"%{q}%")
    ).limit(5)
    rooms = (await db.execute(room_stmt)).all()
    for r, bh in rooms:
        results.append({
            "id": str(r.id),
            "type": "room",
            "title": f"Phòng {r.room_number}",
            "subtitle": bh.name,
            "link": f"/rooms"
        })

    # Search Invoices
    invoice_stmt = select(Invoice).filter(
        Invoice.organization_id == ctx.organization_id,
        Invoice.invoice_number.ilike(f"%{q}%"),
        Invoice.archived_at == None
    ).limit(5)
    invoices = (await db.execute(invoice_stmt)).scalars().all()
    for i in invoices:
        results.append({
            "id": str(i.id),
            "type": "invoice",
            "title": f"Hóa đơn {i.invoice_number}",
            "subtitle": f"Tháng {i.billing_month}/{i.billing_year}",
            "link": f"/invoices"
        })

    return {"items": results}
