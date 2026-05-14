"""
Base Repository - ALL queries automatically filter by organization_id
This ensures tenant isolation at the data layer.
"""
from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import DeclarativeBase

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession, organization_id: str):
        self.model = model
        self.db = db
        self.organization_id = organization_id  # CRITICAL: tenant isolation

    def _tenant_filter(self):
        """Base filter for all queries - ALWAYS applies organization_id"""
        return self.model.organization_id == self.organization_id

    async def get(self, id: str) -> Optional[ModelType]:
        result = await self.db.execute(
            select(self.model).where(
                self.model.id == id,
                self._tenant_filter(),
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        filters: Optional[List] = None,
        order_by=None,
    ) -> List[ModelType]:
        query = select(self.model).where(self._tenant_filter())
        if filters:
            for f in filters:
                query = query.where(f)
        if order_by is not None:
            query = query.order_by(order_by)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(self, filters: Optional[List] = None) -> int:
        query = select(func.count()).select_from(self.model).where(self._tenant_filter())
        if filters:
            for f in filters:
                query = query.where(f)
        result = await self.db.execute(query)
        return result.scalar_one()

    async def create(self, obj_in: Dict[str, Any]) -> ModelType:
        obj_in["organization_id"] = self.organization_id  # Force tenant
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, id: str, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        obj_in.pop("organization_id", None)  # Prevent tenant override
        await self.db.execute(
            update(self.model)
            .where(self.model.id == id, self._tenant_filter())
            .values(**obj_in)
        )
        await self.db.flush()
        return await self.get(id)

    async def delete(self, id: str) -> bool:
        result = await self.db.execute(
            delete(self.model).where(
                self.model.id == id,
                self._tenant_filter(),
            )
        )
        await self.db.flush()
        return result.rowcount > 0

    async def soft_delete(self, id: str) -> Optional[ModelType]:
        return await self.update(id, {"is_active": False})
