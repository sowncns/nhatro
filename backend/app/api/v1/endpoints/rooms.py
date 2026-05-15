"""Rooms API Endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.models.models import Room
from app.schemas.schemas import RoomCreate, RoomUpdate, RoomResponse, PaginatedResponse
from app.repositories.base import BaseRepository
from app.services.cache_service import CacheService

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_rooms(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    boarding_house_id: Optional[str] = None,
    search: Optional[str] = None,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"rooms:list:{ctx.organization_id}:{page}:{size}:{status}:{boarding_house_id}:{search}"
    cached = await CacheService.get(cache_key)
    if cached:
        return cached

    repo = BaseRepository(Room, db, ctx.organization_id)
    filters = []
    if status:
        filters.append(Room.status == status)
    if boarding_house_id:
        filters.append(Room.boarding_house_id == boarding_house_id)
    if search:
        filters.append(Room.room_number.ilike(f"%{search}%"))

    total = await repo.count(filters)
    items = await repo.get_all(
        skip=(page - 1) * size,
        limit=size,
        filters=filters,
        order_by=Room.room_number,
    )
    res = PaginatedResponse(
        items=[RoomResponse.model_validate(r) for r in items],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )
    await CacheService.set(cache_key, res.model_dump(), expire=300)
    return res


@router.post("", response_model=RoomResponse, status_code=201)
async def create_room(
    data: RoomCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(Room, db, ctx.organization_id)
    room_data = data.model_dump()
    billing_settings = ctx.organization.settings or {}
    defaults = {
        "electricity_price": billing_settings.get("default_electricity_price", 4000),
        "water_price": billing_settings.get("default_water_price", 15000),
        "internet_fee": billing_settings.get("default_internet_fee", 0),
        "parking_fee": billing_settings.get("default_parking_fee", 0),
    }
    for key, value in defaults.items():
        if room_data.get(key) is None:
            room_data[key] = value

    room = await repo.create(room_data)
    await CacheService.invalidate(f"rooms:list:{ctx.organization_id}")
    await CacheService.invalidate(f"dashboard:")
    return RoomResponse.model_validate(room)


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(Room, db, ctx.organization_id)
    room = await repo.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return RoomResponse.model_validate(room)


@router.patch("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: str,
    data: RoomUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(Room, db, ctx.organization_id)
    room = await repo.update(room_id, data.model_dump(exclude_none=True))
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    await CacheService.invalidate(f"rooms:list:{ctx.organization_id}")
    await CacheService.invalidate(f"dashboard:")
    return RoomResponse.model_validate(room)


@router.delete("/{room_id}", status_code=204)
async def delete_room(
    room_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(Room, db, ctx.organization_id)
    deleted = await repo.delete(room_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Room not found")
    await CacheService.invalidate(f"rooms:list:{ctx.organization_id}")
    await CacheService.invalidate(f"dashboard:")
