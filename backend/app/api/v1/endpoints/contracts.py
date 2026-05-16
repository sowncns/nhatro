"""Contracts Endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.models.models import Contract, MeterReading, ReadingType, Room, RoomStatus, RoomTenant
from app.schemas.schemas import ContractCreate, ContractResponse, PaginatedResponse, ContractTerminateRequest
from app.repositories.base import BaseRepository
from datetime import datetime
from app.services.cache_service import CacheService
from app.services.contract_termination_service import ContractTerminationService

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_contracts(
    page: int = Query(1, ge=1),
    size: int = Query(20),
    status: str = None,
    mode: str = Query("active"),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"contracts:list:{ctx.organization_id}:{page}:{size}:{status}:{mode}"
    cached = await CacheService.get(cache_key)
    if cached:
        return cached

    repo = BaseRepository(Contract, db, ctx.organization_id)
    filters = []
    if status:
        filters.append(Contract.status == status)
    total = await repo.count(filters, mode=mode)
    items = await repo.get_all(skip=(page - 1) * size, limit=size, filters=filters, mode=mode)
    res = PaginatedResponse(
        items=[ContractResponse.model_validate(c) for c in items],
        total=total, page=page, size=size,
        pages=(total + size - 1) // size,
    )
    await CacheService.set(cache_key, res.model_dump(), expire=300)
    return res


@router.post("", response_model=ContractResponse, status_code=201)
async def create_contract(
    data: ContractCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    if not data.tenant_id or data.tenant_id == "":
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Vui lòng chọn khách thuê cho hợp đồng")
        
    try:
        repo = BaseRepository(Contract, db, ctx.organization_id)

        active_contracts = await repo.get_all(filters=[
            Contract.room_id == data.room_id,
            Contract.status == "ACTIVE",
        ])
        if active_contracts:
            raise HTTPException(status_code=400, detail="Phòng này đang được cho thuê và hợp đồng chưa hết hạn")

        now = datetime.now()
        contract_data = data.model_dump()
        contract_data["contract_number"] = f"HD{now.year}{now.month:02d}{now.microsecond % 10000:04d}"
        contract = await repo.create(contract_data)
     
        # Create MOVE_IN meter reading
        prev_mr_result = await db.execute(
            select(MeterReading).where(MeterReading.room_id == data.room_id).order_by(MeterReading.recorded_at.desc()).limit(1)
        )
        prev_mr = prev_mr_result.scalar_one_or_none()
        
        move_in_mr = MeterReading(
            organization_id=ctx.organization_id,
            room_id=data.room_id,
            contract_id=contract.id,
            reading_type=ReadingType.MOVE_IN,
            period_start=data.start_date,
            period_end=data.start_date,
            reading_month=data.start_date.month,
            reading_year=data.start_date.year,
            electricity_previous=prev_mr.electricity_current if prev_mr else 0,
            electricity_current=prev_mr.electricity_current if prev_mr else 0,
            electricity_usage=0,
            water_previous=prev_mr.water_current if prev_mr else 0,
            water_current=prev_mr.water_current if prev_mr else 0,
            water_usage=0,
            is_locked=True,
            notes=f"Chỉ số bàn giao đầu kỳ - HĐ {contract.contract_number}",
            recorded_by=ctx.user.id
        )
        db.add(move_in_mr)
        await db.flush()

        from app.models.models import Room, RoomStatus, RoomTenant
        room_repo = BaseRepository(Room, db, ctx.organization_id)
        await room_repo.update(data.room_id, {"status": RoomStatus.OCCUPIED})

        tenant_repo = BaseRepository(RoomTenant, db, ctx.organization_id)
        await tenant_repo.create({
            "room_id": data.room_id,
            "tenant_id": data.tenant_id,
            "is_primary": True,
            "move_in_date": data.start_date,
        })
        
        for member_id in data.member_ids:
            await tenant_repo.create({
                "room_id": data.room_id,
                "tenant_id": member_id,
                "is_primary": False,
                "move_in_date": data.start_date,
            })

        await CacheService.invalidate(f"contracts:list:{ctx.organization_id}")
        await CacheService.invalidate(f"rooms:list:{ctx.organization_id}")
        await CacheService.invalidate(f"dashboard:")

        return ContractResponse.model_validate(contract)
    except Exception as e:
        import traceback
        with open("contracts_error.log", "a", encoding="utf-8") as f:
            f.write(f"Error at {datetime.now()}: {e}\n{traceback.format_exc()}\n")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(Contract, db, ctx.organization_id)
    contract = await repo.get(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return ContractResponse.model_validate(contract)


@router.post("/{contract_id}/terminate", response_model=ContractResponse)
async def terminate_contract(
    contract_id: str,
    data: ContractTerminateRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    service = ContractTerminationService(db, ctx.organization_id, ctx.user.id)
    contract = await service.terminate_contract(contract_id, data)
    
    await CacheService.invalidate(f"contracts:list:{ctx.organization_id}")
    await CacheService.invalidate(f"rooms:list:{ctx.organization_id}")
    await CacheService.invalidate(f"dashboard:")
    
    return ContractResponse.model_validate(contract)


@router.post("/{contract_id}/cancel", response_model=ContractResponse)
async def cancel_contract(
    contract_id: str,
    reason: str = "Chủ trọ hủy hợp đồng",
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    service = ContractTerminationService(db, ctx.organization_id, ctx.user.id)
    contract = await service.cancel_contract(contract_id, reason)
    
    await CacheService.invalidate(f"contracts:list:{ctx.organization_id}")
    await CacheService.invalidate(f"rooms:list:{ctx.organization_id}")
    await CacheService.invalidate(f"dashboard:")
    
    return ContractResponse.model_validate(contract)
