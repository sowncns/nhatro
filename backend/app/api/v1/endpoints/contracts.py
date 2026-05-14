"""Contracts Endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.models.models import Contract
from app.schemas.schemas import ContractCreate, ContractResponse, PaginatedResponse
from app.repositories.base import BaseRepository
from datetime import datetime

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_contracts(
    page: int = Query(1, ge=1),
    size: int = Query(20),
    status: str = None,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(Contract, db, ctx.organization_id)
    filters = []
    if status:
        filters.append(Contract.status == status)
    total = await repo.count(filters)
    items = await repo.get_all(skip=(page - 1) * size, limit=size, filters=filters)
    return PaginatedResponse(
        items=[ContractResponse.model_validate(c) for c in items],
        total=total, page=page, size=size,
        pages=(total + size - 1) // size,
    )


@router.post("", response_model=ContractResponse, status_code=201)
async def create_contract(
    data: ContractCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(Contract, db, ctx.organization_id)
    now = datetime.now()
    contract_data = data.model_dump()
    contract_data["contract_number"] = f"HD{now.year}{now.month:02d}{now.microsecond % 10000:04d}"
    contract = await repo.create(contract_data)

    # Update room status to occupied
    from app.models.models import Room, RoomStatus
    room_repo = BaseRepository(Room, db, ctx.organization_id)
    await room_repo.update(data.room_id, {"status": RoomStatus.OCCUPIED})

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
        from fastapi import HTTPException
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
        from app.models.models import Room, RoomStatus
        room_repo = BaseRepository(Room, db, ctx.organization_id)
        await room_repo.update(contract.room_id, {"status": RoomStatus.AVAILABLE})
    return {"message": "Contract terminated"}
