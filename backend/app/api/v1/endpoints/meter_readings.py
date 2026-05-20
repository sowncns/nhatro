"""Meter Readings Endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.models.models import MeterReading, Contract, ContractStatus
from app.schemas.schemas import MeterReadingCreate, MeterReadingUpdate, MeterReadingResponse, PaginatedResponse
from app.repositories.base import BaseRepository
from app.services.cache_service import CacheService
from app.services.invalidate_helper import InvalidateHelper
from app.core.cache_constants import TTL_UTILITY_LIST

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_meter_readings(
    page: int = Query(1, ge=1),
    size: int = Query(20),
    room_id: str = None,
    contract_id: str = None,
    month: int = None,
    year: int = None,
    mode: str = Query("active"),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"mr:list:{ctx.organization_id}:{page}:{size}:{room_id}:{month}:{year}:{mode}"
    cached = await CacheService.get(cache_key)
    if cached:
        return cached

    repo = BaseRepository(MeterReading, db, ctx.organization_id)
    filters = []
    if room_id:
        filters.append(MeterReading.room_id == room_id)
    if contract_id:
        filters.append(MeterReading.contract_id == contract_id)
    if month:
        filters.append(MeterReading.reading_month == month)
    if year:
        filters.append(MeterReading.reading_year == year)
    total = await repo.count(filters, mode=mode)
    items = await repo.get_all(skip=(page - 1) * size, limit=size, filters=filters, mode=mode)
    res = PaginatedResponse(
        items=[MeterReadingResponse.model_validate(r) for r in items],
        total=total, page=page, size=size,
        pages=(total + size - 1) // size,
    )
    await CacheService.set(cache_key, res.model_dump(), expire=TTL_UTILITY_LIST)
    return res


@router.post("", response_model=MeterReadingResponse, status_code=201)
async def create_meter_reading(
    data: MeterReadingCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    try:
        # 1. Resolve contract if not provided
        contract_id = data.contract_id
        if not contract_id:
            contract_result = await db.execute(
                select(Contract).where(
                    Contract.room_id == data.room_id,
                    Contract.organization_id == ctx.organization_id,
                    Contract.status == ContractStatus.ACTIVE
                ).limit(1)
            )
            contract = contract_result.scalar_one_or_none()
            if contract:
                contract_id = contract.id

        # 2. Get previous reading for continuity validation
        previous_result = await db.execute(
            select(MeterReading)
            .where(
                MeterReading.organization_id == ctx.organization_id,
                MeterReading.room_id == data.room_id,
            )
            .order_by(MeterReading.recorded_at.desc())
            .limit(1)
        )
        previous = previous_result.scalar_one_or_none()

        elec_prev = data.electricity_previous if data.electricity_previous is not None else (previous.electricity_current if previous else 0)
        water_prev = data.water_previous if data.water_previous is not None else (previous.water_current if previous else 0)

        # 3. Validation
        if data.electricity_current < elec_prev:
            raise HTTPException(status_code=400, detail=f"Chỉ số điện mới ({data.electricity_current}) không được nhỏ hơn chỉ số cũ ({elec_prev})")
        if data.water_current < water_prev:
            raise HTTPException(status_code=400, detail=f"Chỉ số nước mới ({data.water_current}) không được nhỏ hơn chỉ số cũ ({water_prev})")

        # Check if reading already exists for this room, month and year
        existing_reading_result = await db.execute(
            select(MeterReading).where(
                MeterReading.room_id == data.room_id,
                MeterReading.reading_month == data.reading_month,
                MeterReading.reading_year == data.reading_year,
                MeterReading.organization_id == ctx.organization_id,
                MeterReading.archived_at.is_(None)
            )
        )
        existing_reading = existing_reading_result.scalars().first()
        
        if existing_reading:
            # Overwrite!
            existing_reading.electricity_current = data.electricity_current
            existing_reading.water_current = data.water_current
            existing_reading.electricity_usage = data.electricity_current - existing_reading.electricity_previous
            existing_reading.water_usage = data.water_current - existing_reading.water_previous
            existing_reading.recorded_by = ctx.user.id
            
            await db.flush()
            await db.refresh(existing_reading)
            
            await InvalidateHelper.invalidate_utility(ctx.organization_id, existing_reading.id)
            
            return MeterReadingResponse.model_validate(existing_reading)

        # 4. Save new
        repo = BaseRepository(MeterReading, db, ctx.organization_id)
        reading_data = data.model_dump()
        reading_data.update({
            "contract_id": contract_id,
            "electricity_previous": elec_prev,
            "water_previous": water_prev,
            "electricity_usage": data.electricity_current - elec_prev,
            "water_usage": data.water_current - water_prev,
            "recorded_by": ctx.user.id
        })
        
        reading = await repo.create(reading_data)

        await InvalidateHelper.invalidate_utility(ctx.organization_id, reading.id)

        return MeterReadingResponse.model_validate(reading)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        from datetime import datetime
        with open("contracts_error.log", "a", encoding="utf-8") as f:
            f.write(f"Error at {datetime.now()}: {e}\n{traceback.format_exc()}\n")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{id}", response_model=MeterReadingResponse)
async def update_meter_reading(
    id: str,
    data: MeterReadingUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    try:
        repo = BaseRepository(MeterReading, db, ctx.organization_id)
        reading = await repo.get(id)
        if not reading:
            raise HTTPException(status_code=404, detail="Reading not found")

        if reading.is_locked:
            raise HTTPException(status_code=400, detail="Chỉ số đã chốt hóa đơn, không thể sửa đổi")

        update_data = data.model_dump(exclude_unset=True)

        elec_prev = update_data.get("electricity_previous", reading.electricity_previous)
        elec_curr = update_data.get("electricity_current", reading.electricity_current)
        water_prev = update_data.get("water_previous", reading.water_previous)
        water_curr = update_data.get("water_current", reading.water_current)

        if elec_curr < elec_prev:
            raise HTTPException(status_code=400, detail="Chỉ số mới không được nhỏ hơn chỉ số cũ")
        if water_curr < water_prev:
            raise HTTPException(status_code=400, detail="Chỉ số mới không được nhỏ hơn chỉ số cũ")

        update_data["electricity_usage"] = elec_curr - elec_prev
        update_data["water_usage"] = water_curr - water_prev

        updated = await repo.update(id, update_data)

        await InvalidateHelper.invalidate_utility(ctx.organization_id, id)

        return MeterReadingResponse.model_validate(updated)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        from datetime import datetime
        with open("contracts_error.log", "a", encoding="utf-8") as f:
            f.write(f"Error at {datetime.now()} (update): {e}\n{traceback.format_exc()}\n")
        raise HTTPException(status_code=500, detail=str(e))
