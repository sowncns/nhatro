"""Contracts Endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.models.models import Contract
from app.schemas.schemas import ContractCreate, ContractResponse, PaginatedResponse
from app.repositories.base import BaseRepository
from datetime import datetime
from app.services.cache_service import CacheService

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_contracts(
    page: int = Query(1, ge=1),
    size: int = Query(20),
    status: str = None,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"contracts:list:{ctx.organization_id}:{page}:{size}:{status}"
    cached = await CacheService.get(cache_key)
    if cached:
        return cached

    repo = BaseRepository(Contract, db, ctx.organization_id)
    filters = []
    if status:
        filters.append(Contract.status == status)
    total = await repo.count(filters)
    items = await repo.get_all(skip=(page - 1) * size, limit=size, filters=filters)
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
    repo = BaseRepository(Contract, db, ctx.organization_id)

    active_contracts = await repo.get_all(filters=[
        Contract.room_id == data.room_id,
        Contract.status == "active",
    ])
    if active_contracts:
        raise HTTPException(status_code=400, detail="Phòng này đang được cho thuê và hợp đồng chưa hết hạn")

    now = datetime.now()
    contract_data = data.model_dump()
    contract_data["contract_number"] = f"HD{now.year}{now.month:02d}{now.microsecond % 10000:04d}"
    contract = await repo.create(contract_data)

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


@router.post("/{contract_id}/terminate")
async def terminate_contract(
    contract_id: str,
    reason: str = "",
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    from datetime import timezone
    repo = BaseRepository(Contract, db, ctx.organization_id)
    contract = await repo.update(contract_id, {
        "status": "terminated",
        "terminated_at": datetime.now(timezone.utc),
        "termination_reason": reason,
    })
    if contract:
        from app.models.models import Room, RoomStatus, RoomTenant
        room_repo = BaseRepository(Room, db, ctx.organization_id)
        await room_repo.update(contract.room_id, {"status": RoomStatus.AVAILABLE})

        tenant_repo = BaseRepository(RoomTenant, db, ctx.organization_id)
        room_tenants = await tenant_repo.get_all(filters=[RoomTenant.room_id == contract.room_id, RoomTenant.is_active == True])
        for rt in room_tenants:
            await tenant_repo.update(str(rt.id), {"is_active": False, "move_out_date": datetime.now(timezone.utc).date()})

        await CacheService.invalidate(f"contracts:list:{ctx.organization_id}")
        await CacheService.invalidate(f"rooms:list:{ctx.organization_id}")
        await CacheService.invalidate(f"dashboard:")

    return {"message": "Contract terminated"}
