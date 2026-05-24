"""Dashboard Service - Analytics and Statistics"""
from datetime import datetime, date
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.models import Room, RoomStatus, Tenant, Invoice, InvoiceStatus, Contract, RoomTenant, MaintenanceRequest, MaintenanceStatus
from app.schemas.schemas import DashboardStats


class DashboardService:
    def __init__(self, db: AsyncSession, organization_id: str):
        self.db = db
        self.organization_id = organization_id

    async def get_stats(self) -> DashboardStats:
        now = datetime.now()
        oid = self.organization_id

        # Room stats
        rooms = await self.db.execute(
            select(Room.status, func.count(Room.id))
            .where(
                Room.organization_id == oid,
                # Room không có archived_at hiện tại nhưng có thể thêm sau này nếu cần
            )
            .group_by(Room.status)
        )
        room_counts = {row[0]: row[1] for row in rooms}
        total_rooms = sum(room_counts.values())
        occupied = room_counts.get(RoomStatus.OCCUPIED, 0)
        available = room_counts.get(RoomStatus.AVAILABLE, 0)
        occupancy_rate = (occupied / total_rooms * 100) if total_rooms > 0 else 0

        # Tenant count
        tenant_result = await self.db.execute(
            select(func.count(Tenant.id)).where(
                Tenant.organization_id == oid,
                Tenant.is_active == True,
                Tenant.archived_at == None
            )
        )
        total_tenants = tenant_result.scalar_one() or 0

        # Monthly revenue (paid invoices this month)
        revenue_result = await self.db.execute(
            select(func.sum(Invoice.paid_amount)).where(
                Invoice.organization_id == oid,
                Invoice.billing_month == now.month,
                Invoice.billing_year == now.year,
                Invoice.status == 'PAID',
                Invoice.archived_at == None
            )
        )
        invoice_revenue = revenue_result.scalar_one() or 0

        # Deposit deductions (forfeited deposits, penalty fees deducted from deposit)
        from app.database.models import DepositTransaction, DepositAction
        from sqlalchemy import extract
        deposit_revenue_result = await self.db.execute(
            select(func.sum(DepositTransaction.amount)).where(
                DepositTransaction.organization_id == oid,
                extract('month', DepositTransaction.created_at) == now.month,
                extract('year', DepositTransaction.created_at) == now.year,
                DepositTransaction.type == DepositAction.DEDUCTION
            )
        )
        deposit_revenue = deposit_revenue_result.scalar_one() or 0
        
        monthly_revenue = invoice_revenue + deposit_revenue

        # Outstanding debt
        outstanding_result = await self.db.execute(
            select(func.sum(Invoice.total_amount - Invoice.paid_amount)).where(
                Invoice.organization_id == oid,
                Invoice.status.in_(['SENT', 'OVERDUE']),
                Invoice.archived_at == None
            )
        )
        outstanding = outstanding_result.scalar_one() or 0

        # Contracts expiring in next 30 days
        from datetime import timedelta
        expire_date = date.today() + timedelta(days=30)
        expiring_result = await self.db.execute(
            select(func.count(Contract.id)).where(
                Contract.organization_id == oid,
                Contract.status == "ACTIVE",
                Contract.end_date <= expire_date,
                Contract.archived_at == None
            )
        )
        expiring = expiring_result.scalar_one() or 0

        # Maintenance stats
        maintenance_result = await self.db.execute(
            select(func.count(MaintenanceRequest.id)).where(
                MaintenanceRequest.organization_id == oid,
                MaintenanceRequest.status.in_(['PENDING', 'IN_PROGRESS']),
                MaintenanceRequest.archived_at == None
            )
        )
        pending_maintenance = maintenance_result.scalar_one() or 0

        return DashboardStats(
            total_rooms=total_rooms,
            occupied_rooms=occupied,
            available_rooms=available,
            occupancy_rate=round(occupancy_rate, 1),
            total_tenants=total_tenants,
            total_revenue_month=monthly_revenue,
            total_outstanding=outstanding,
            expiring_contracts=expiring,
            pending_maintenance=pending_maintenance,
        )

    async def get_monthly_revenue(self, year: int) -> List[Dict]:
        """Revenue by month for a given year"""
        result = await self.db.execute(
            select(
                Invoice.billing_month,
                func.sum(Invoice.paid_amount).label("revenue"),
                func.sum(Invoice.total_amount).label("billed"),
            )
            .where(
                Invoice.organization_id == self.organization_id,
                Invoice.billing_year == year,
            )
            .group_by(Invoice.billing_month)
            .order_by(Invoice.billing_month)
        )
        
        from app.database.models import DepositTransaction, DepositAction
        from sqlalchemy import extract
        deposit_result = await self.db.execute(
            select(
                extract('month', DepositTransaction.created_at).label("month"),
                func.sum(DepositTransaction.amount).label("revenue"),
            )
            .where(
                DepositTransaction.organization_id == self.organization_id,
                extract('year', DepositTransaction.created_at) == year,
                DepositTransaction.type == DepositAction.DEDUCTION
            )
            .group_by(extract('month', DepositTransaction.created_at))
        )
        
        months = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12"]
        data = {row[0]: {"revenue": row[1] or 0, "billed": row[2] or 0} for row in result}
        deposit_data = {int(row[0]): row[1] or 0 for row in deposit_result}
        
        return [
            {
                "month": months[i],
                "month_number": i + 1,
                "revenue": data.get(i + 1, {}).get("revenue", 0) + deposit_data.get(i + 1, 0),
                "billed": data.get(i + 1, {}).get("billed", 0) + deposit_data.get(i + 1, 0),
            }
            for i in range(12)
        ]

    async def get_room_occupancy_trend(self) -> List[Dict]:
        """Occupancy by boarding house"""
        from app.models.models import BoardingHouse
        result = await self.db.execute(
            select(
                BoardingHouse.name,
                func.count(Room.id).label("total"),
                func.sum(func.cast(Room.status == RoomStatus.OCCUPIED, func.Integer)).label("occupied"),
            )
            .join(Room, Room.boarding_house_id == BoardingHouse.id)
            .where(BoardingHouse.organization_id == self.organization_id)
            .group_by(BoardingHouse.id, BoardingHouse.name)
        )
        return [
            {
                "name": row[0],
                "total": row[1],
                "occupied": row[2] or 0,
                "rate": round((row[2] or 0) / row[1] * 100, 1) if row[1] > 0 else 0,
            }
            for row in result
        ]
