from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_platform_admin
from app.database.session import get_db
from app.models.models import User
from app.schemas.schemas import PlatformCustomerResponse, PlatformStatsResponse, SaaSPaymentResponse
from app.services.billing_service import BillingService

router = APIRouter()


@router.get("/stats", response_model=PlatformStatsResponse)
async def platform_stats(
    _: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    service = BillingService(db)
    return await service.platform_stats()


@router.get("/customers", response_model=list[PlatformCustomerResponse])
async def platform_customers(
    _: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    service = BillingService(db)
    return await service.list_customers()


@router.get("/payments", response_model=list[SaaSPaymentResponse])
async def platform_payments(
    status: str | None = Query(default=None),
    _: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    service = BillingService(db)
    return await service.list_payments(status)


@router.post("/payments/{payment_id}/approve", response_model=SaaSPaymentResponse)
async def approve_payment(
    payment_id: str,
    admin: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    service = BillingService(db)
    return await service.mark_payment_paid(payment_id, admin_user=admin)
