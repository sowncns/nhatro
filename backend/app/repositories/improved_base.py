"""Improved Base Repository with soft delete support and better query optimization"""
from typing import TypeVar, Generic, List, Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from fastapi import HTTPException

from app.database.mixins import SoftDeleteMixin

T = TypeVar('T')


class ImprovedBaseRepository(Generic[T]):
    """
    Enhanced base repository with:
    - Soft delete support
    - Eager loading optimization
    - Better filtering
    - Transaction support
    """

    def __init__(self, model: type[T], db: AsyncSession, organization_id: str):
        self.model = model
        self.db = db
        self.organization_id = organization_id

    def _base_query(self, include_archived: bool = False):
        """Base query with organization filter and soft delete handling"""
        query = select(self.model).where(self.model.organization_id == self.organization_id)

        # Apply soft delete filter if model supports it
        if hasattr(self.model, 'is_archived') and not include_archived:
            query = query.where(self.model.is_archived == False)

        return query

    async def get(
        self,
        id: str,
        include_archived: bool = False,
        eager_load: Optional[List[str]] = None
    ) -> Optional[T]:
        """Get single record by ID with optional eager loading"""
        query = self._base_query(include_archived).where(self.model.id == id)

        # Apply eager loading
        if eager_load:
            for relation in eager_load:
                query = query.options(selectinload(getattr(self.model, relation)))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[List] = None,
        order_by: Optional[Any] = None,
        include_archived: bool = False,
        eager_load: Optional[List[str]] = None
    ) -> List[T]:
        """Get all records with pagination and filters"""
        query = self._base_query(include_archived)

        # Apply additional filters
        if filters:
            query = query.where(and_(*filters))

        # Apply ordering
        if order_by is not None:
            query = query.order_by(order_by)
        else:
            # Default ordering by created_at if available
            if hasattr(self.model, 'created_at'):
                query = query.order_by(self.model.created_at.desc())

        # Apply eager loading
        if eager_load:
            for relation in eager_load:
                query = query.options(selectinload(getattr(self.model, relation)))

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        filters: Optional[List] = None,
        include_archived: bool = False
    ) -> int:
        """Count records with filters"""
        query = select(func.count()).select_from(self.model).where(
            self.model.organization_id == self.organization_id
        )

        # Apply soft delete filter
        if hasattr(self.model, 'is_archived') and not include_archived:
            query = query.where(self.model.is_archived == False)

        # Apply additional filters
        if filters:
            query = query.where(and_(*filters))

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def create(self, data: Dict[str, Any]) -> T:
        """Create new record"""
        # Ensure organization_id is set
        data['organization_id'] = self.organization_id

        # Create instance
        instance = self.model(**data)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        """Update existing record"""
        instance = await self.get(id)
        if not instance:
            return None

        # Update fields
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete(self, id: str, hard_delete: bool = False) -> bool:
        """
        Delete record (soft delete by default if supported)

        Args:
            id: Record ID
            hard_delete: If True, permanently delete. If False, soft delete.

        Returns:
            True if deleted, False if not found
        """
        instance = await self.get(id, include_archived=True)
        if not instance:
            return False

        if hard_delete or not isinstance(instance, SoftDeleteMixin):
            # Hard delete
            await self.db.delete(instance)
        else:
            # Soft delete
            instance.soft_delete()

        await self.db.flush()
        return True

    async def restore(self, id: str) -> Optional[T]:
        """Restore soft-deleted record"""
        instance = await self.get(id, include_archived=True)
        if not instance or not isinstance(instance, SoftDeleteMixin):
            return None

        instance.restore()
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[T]:
        """Bulk create records"""
        instances = []
        for data in data_list:
            data['organization_id'] = self.organization_id
            instance = self.model(**data)
            self.db.add(instance)
            instances.append(instance)

        await self.db.flush()
        for instance in instances:
            await self.db.refresh(instance)

        return instances

    async def exists(self, filters: List) -> bool:
        """Check if record exists with given filters"""
        query = select(func.count()).select_from(self.model).where(
            self.model.organization_id == self.organization_id
        )

        if hasattr(self.model, 'is_archived'):
            query = query.where(self.model.is_archived == False)

        query = query.where(and_(*filters))

        result = await self.db.execute(query)
        count = result.scalar() or 0
        return count > 0

    async def get_or_create(
        self,
        filters: List,
        defaults: Optional[Dict[str, Any]] = None
    ) -> tuple[T, bool]:
        """
        Get existing record or create new one

        Returns:
            (instance, created) where created is True if new record was created
        """
        # Try to get existing
        query = self._base_query().where(and_(*filters))
        result = await self.db.execute(query)
        instance = result.scalar_one_or_none()

        if instance:
            return instance, False

        # Create new
        data = defaults or {}
        for filter_clause in filters:
            # Extract column and value from filter
            if hasattr(filter_clause, 'left') and hasattr(filter_clause, 'right'):
                col_name = filter_clause.left.key
                value = filter_clause.right.value
                data[col_name] = value

        instance = await self.create(data)
        return instance, True
