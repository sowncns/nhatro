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

    def _apply_view_mode(self, query, mode: str = "active"):
        """Applies filters based on active/history/archived modes"""
        # Default: Exclude archived if column exists
        if hasattr(self.model, 'archived_at'):
            if mode == "archived":
                return query.where(self.model.archived_at != None)
            query = query.where(self.model.archived_at == None)
        
        # Entity-specific status filtering
        from app.database.models import Contract, Invoice, MaintenanceRequest, Tenant, MeterReading, ContractStatus, InvoiceStatus, MaintenanceStatus
        model_name = self.model.__name__
        
        if mode == "active":
            if model_name == "Contract":
                query = query.where(Contract.status.in_([ContractStatus.ACTIVE, ContractStatus.DRAFT]))
            elif model_name == "Invoice":
                query = query.where(Invoice.status.in_([InvoiceStatus.DRAFT, InvoiceStatus.SENT, InvoiceStatus.OVERDUE, InvoiceStatus.WAITING_VERIFY]))
            elif model_name == "MaintenanceRequest":
                query = query.where(MaintenanceRequest.status.in_([MaintenanceStatus.PENDING, MaintenanceStatus.IN_PROGRESS]))
            elif model_name == "Tenant":
                query = query.where(Tenant.is_active == True)
            elif model_name == "MeterReading":
                # Chỉ hiển thị chỉ số của tháng hiện tại
                from datetime import datetime
                now = datetime.now()
                query = query.where(
                    MeterReading.reading_month == now.month,
                    MeterReading.reading_year == now.year
                )
        
        elif mode == "history":
            if model_name == "Contract":
                query = query.where(Contract.status.in_([ContractStatus.ENDED, ContractStatus.CANCELLED, ContractStatus.EXPIRED, ContractStatus.TERMINATED]))
            elif model_name == "Invoice":
                query = query.where(Invoice.status.in_([InvoiceStatus.PAID, InvoiceStatus.CANCELLED]))
            elif model_name == "MaintenanceRequest":
                query = query.where(MaintenanceRequest.status.in_([MaintenanceStatus.RESOLVED, MaintenanceStatus.CANCELLED]))
            elif model_name == "Tenant":
                query = query.where(Tenant.is_active == False)
            elif model_name == "MeterReading":
                query = query.where(MeterReading.is_locked == True)
                
        return query

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
        mode: str = "active",
    ) -> List[ModelType]:
        query = select(self.model).where(self._tenant_filter())
        query = self._apply_view_mode(query, mode)
        if filters:
            for f in filters:
                query = query.where(f)
        if order_by is not None:
            query = query.order_by(order_by)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(self, filters: Optional[List] = None, mode: str = "active") -> int:
        query = select(func.count()).select_from(self.model).where(self._tenant_filter())
        query = self._apply_view_mode(query, mode)
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
