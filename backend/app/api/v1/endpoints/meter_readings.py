"""Meter Readings Endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.models.models import MeterReading
from app.schemas.schemas import MeterReadingCreate, MeterReadingUpdate, MeterReadingResponse, PaginatedResponse
from app.repositories.base import BaseRepository
from app.services.cache_service import CacheService

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_meter_readings(
    page: int = Query(1, ge=1),
    size: int = Query(20),
    room_id: str = None,
    month: int = None,
    year: int = None,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"mr:list:{ctx.organization_id}:{page}:{size}:{room_id}:{month}:{year}"
    cached = await CacheService.get(cache_key)
    if cached:
        return cached

    repo = BaseRepository(MeterReading, db, ctx.organization_id)
    filters = []
    if room_id:
        filters.append(MeterReading.room_id == room_id)
    if month:
        filters.append(MeterReading.reading_month == month)
    if year:
        filters.append(MeterReading.reading_year == year)
    total = await repo.count(filters)
    items = await repo.get_all(skip=(page - 1) * size, limit=size, filters=filters)
    res = PaginatedResponse(
        items=[MeterReadingResponse.model_validate(r) for r in items],
        total=total, page=page, size=size,
        pages=(total + size - 1) // size,
    )
    await CacheService.set(cache_key, res.model_dump(), expire=300)
    return res


@router.post("", response_model=MeterReadingResponse, status_code=201)
async def create_meter_reading(
    data: MeterReadingCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(MeterReading, db, ctx.organization_id)
    reading_data = data.model_dump()
    previous_result = await db.execute(
        select(MeterReading)
        .where(
            MeterReading.organization_id == ctx.organization_id,
            MeterReading.room_id == data.room_id,
        )
        .order_by(MeterReading.reading_year.desc(), MeterReading.reading_month.desc())
        .limit(1)
    )
    previous = previous_result.scalar_one_or_none()

    electricity_previous = (
        data.electricity_previous
        if data.electricity_previous is not None
        else previous.electricity_current if previous else 0
    )
    water_previous = (
        data.water_previous
        if data.water_previous is not None
        else previous.water_current if previous else 0
    )

    reading_data["electricity_previous"] = electricity_previous
    reading_data["water_previous"] = water_previous
    reading_data["electricity_usage"] = data.electricity_current - electricity_previous
    reading_data["water_usage"] = data.water_current - water_previous
    reading_data["recorded_by"] = ctx.user.id
    reading = await repo.create(reading_data)

    await CacheService.invalidate(f"mr:list:{ctx.organization_id}")
    await CacheService.invalidate(f"dashboard:")

    return MeterReadingResponse.model_validate(reading)


@router.patch("/{id}", response_model=MeterReadingResponse)
async def update_meter_reading(
    id: str,
    data: MeterReadingUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(MeterReading, db, ctx.organization_id)
    reading = await repo.get_by_id(id)
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")

    update_data = data.model_dump(exclude_unset=True)

    elec_prev = update_data.get("electricity_previous", reading.electricity_previous)
    elec_curr = update_data.get("electricity_current", reading.electricity_current)
    water_prev = update_data.get("water_previous", reading.water_previous)
    water_curr = update_data.get("water_current", reading.water_current)

    if elec_prev is not None and elec_curr is not None:
        update_data["electricity_usage"] = elec_curr - elec_prev
    if water_prev is not None and water_curr is not None:
        update_data["water_usage"] = water_curr - water_curr

    updated = await repo.update(id, update_data)

    await CacheService.invalidate(f"mr:list:{ctx.organization_id}")
    await CacheService.invalidate(f"dashboard:")

    return MeterReadingResponse.model_validate(updated)
