"""Meter Readings Endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.models.models import MeterReading
from app.schemas.schemas import MeterReadingCreate, MeterReadingResponse, PaginatedResponse
from app.repositories.base import BaseRepository

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
    return PaginatedResponse(
        items=[MeterReadingResponse.model_validate(r) for r in items],
        total=total, page=page, size=size,
        pages=(total + size - 1) // size,
    )


@router.post("", response_model=MeterReadingResponse, status_code=201)
async def create_meter_reading(
    data: MeterReadingCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(MeterReading, db, ctx.organization_id)
    reading_data = data.model_dump()
    reading_data["electricity_usage"] = data.electricity_current - data.electricity_previous
    reading_data["water_usage"] = data.water_current - data.water_previous
    reading_data["recorded_by"] = ctx.user.id
    reading = await repo.create(reading_data)
    return MeterReadingResponse.model_validate(reading)
