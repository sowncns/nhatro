"""Boarding Houses Endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.models.models import BoardingHouse
from app.schemas.schemas import BoardingHouseCreate, BoardingHouseUpdate, BoardingHouseResponse, PaginatedResponse
from app.repositories.base import BaseRepository

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_boarding_houses(
    page: int = Query(1, ge=1),
    size: int = Query(20),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(BoardingHouse, db, ctx.organization_id)
    total = await repo.count()
    items = await repo.get_all(skip=(page - 1) * size, limit=size)
    return PaginatedResponse(
        items=[BoardingHouseResponse.model_validate(i) for i in items],
        total=total, page=page, size=size,
        pages=(total + size - 1) // size,
    )


@router.post("", response_model=BoardingHouseResponse, status_code=201)
async def create_boarding_house(
    data: BoardingHouseCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(BoardingHouse, db, ctx.organization_id)
    bh = await repo.create(data.model_dump())
    return BoardingHouseResponse.model_validate(bh)


@router.get("/{bh_id}", response_model=BoardingHouseResponse)
async def get_boarding_house(
    bh_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(BoardingHouse, db, ctx.organization_id)
    bh = await repo.get(bh_id)
    if not bh:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Boarding house not found")
    return BoardingHouseResponse.model_validate(bh)


@router.patch("/{bh_id}", response_model=BoardingHouseResponse)
async def update_boarding_house(
    bh_id: str,
    data: BoardingHouseUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(BoardingHouse, db, ctx.organization_id)
    bh = await repo.update(bh_id, data.model_dump(exclude_none=True))
    if not bh:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")
    return BoardingHouseResponse.model_validate(bh)


@router.delete("/{bh_id}", status_code=204)
async def delete_boarding_house(
    bh_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(BoardingHouse, db, ctx.organization_id)
    await repo.soft_delete(bh_id)
