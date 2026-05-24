"""Contracts Endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.models.models import Contract, MeterReading, ReadingType, Room, RoomStatus, RoomTenant
from app.schemas.schemas import (
    ContractCreate,
    ContractResponse,
    PaginatedResponse,
    ContractTerminateRequest,
    TerminationExecuteRequest,
    TerminationExecuteResponse,
    TerminationHistoryResponse,
)
from app.repositories.base import BaseRepository
from datetime import datetime
from app.services.cache_service import CacheService
from app.services.invalidate_helper import InvalidateHelper
from app.core.cache_constants import TTL_CONTRACT_LIST, TTL_CONTRACT_DETAIL
from app.services.contract_termination_service import ContractTerminationService
from app.services.termination_service import TerminationService
from app.services.termination_query_service import TerminationQueryService

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
    await CacheService.set(cache_key, res.model_dump(), expire=TTL_CONTRACT_LIST)
    return res


@router.post("", response_model=ContractResponse, status_code=201)
async def create_contract(
    data: ContractCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    if not data.tenant_id or data.tenant_id == "":
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
        
        await InvalidateHelper.invalidate_contract(ctx.organization_id)

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
    cache_key = f"contracts:detail:{ctx.organization_id}:{contract_id}"
    cached = await CacheService.get(cache_key)
    if cached:
        return cached

    repo = BaseRepository(Contract, db, ctx.organization_id)
    contract = await repo.get(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    res = ContractResponse.model_validate(contract)
    await CacheService.set(cache_key, res.model_dump(), expire=TTL_CONTRACT_DETAIL)
    return res


@router.post("/{contract_id}/terminate", response_model=ContractResponse)
async def terminate_contract(
    contract_id: str,
    data: ContractTerminateRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    service = ContractTerminationService(db, ctx.organization_id, ctx.user.id)
    contract = await service.terminate_contract(contract_id, data)
    
    await InvalidateHelper.invalidate_contract(ctx.organization_id, contract_id)
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
    
    await InvalidateHelper.invalidate_contract(ctx.organization_id, contract_id)
    return ContractResponse.model_validate(contract)


@router.post("/{contract_id}/terminate-v2", response_model=TerminationExecuteResponse)
async def terminate_contract_v2(
    contract_id: str,
    data: TerminationExecuteRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    from app.database.models import TerminationType

    try:
        ttype = TerminationType[data.termination_type]
    except Exception:
        raise HTTPException(status_code=400, detail="termination_type không hợp lệ")

    service = TerminationService(db, ctx.organization_id, ctx.user.id)
    res = await service.execute(
        contract_id=contract_id,
        termination_type=ttype,
        reason=data.reason,
        note=data.note,
        actual_end_date=data.actual_end_date,
        final_electricity=data.final_electricity,
        final_water=data.final_water,
        penalty_fee=data.penalty_fee,
        damage_fee=data.damage_fee,
        cleaning_fee=data.cleaning_fee,
        other_fee=data.other_fee,
        refund_unused_rent=data.refund_unused_rent,
        compensation_fee=data.compensation_fee,
        force=data.force,
        metadata=data.metadata,
    )

    await InvalidateHelper.invalidate_contract(ctx.organization_id, contract_id)
    await InvalidateHelper.invalidate_invoice(ctx.organization_id)
    return TerminationExecuteResponse(
        contractId=res.contract_id,
        contractStatus=res.contract_status,
        terminationType=res.termination_type,
        terminationReason=res.termination_reason,
        invoiceId=res.invoice_id,
        invoiceStatus=res.invoice_status,
        usedMoney=res.used_money,
        utilityFee=res.utility_fee,
        penaltyFee=res.penalty_fee,
        damageFee=res.damage_fee,
        depositUsed=res.deposit_used,
        refundAmount=res.refund_amount,
        remainingDebt=res.remaining_debt,
        needManualReview=res.need_manual_review,
        terminatedAt=res.terminated_at,
        terminatedBy=res.terminated_by,
        message=res.message,
    )


@router.get("/{contract_id}/termination-history", response_model=list[TerminationHistoryResponse])
async def list_termination_history(
    contract_id: str,
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    service = TerminationQueryService(db, ctx.organization_id)
    items = await service.list_for_contract(contract_id, limit=limit)
    return [TerminationHistoryResponse.model_validate(x) for x in items]
