from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TenantContext, require_owner
from app.database.session import get_db
from app.schemas.schemas import BillingOverview, CheckoutRequest, CheckoutResponse, SaaSPaymentResponse
from app.services.billing_service import BillingService

router = APIRouter()


@router.get("/overview", response_model=BillingOverview)
async def billing_overview(
    ctx: TenantContext = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    service = BillingService(db)
    return await service.get_overview(ctx.organization)


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    data: CheckoutRequest,
    ctx: TenantContext = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    service = BillingService(db)
    return await service.create_checkout(
        organization=ctx.organization,
        user=ctx.user,
        plan=data.plan,
        feature_key=data.feature_key,
        provider=data.provider,
    )


@router.post("/payments/{payment_id}/simulate-paid", response_model=SaaSPaymentResponse)
async def simulate_owner_payment(
    payment_id: str,
    ctx: TenantContext = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Development helper: mark the owner's own checkout as paid.

    In production this should be replaced by payment-provider webhooks.
    """
    service = BillingService(db)
    return await service.mark_payment_paid(payment_id, organization_id=ctx.organization_id)
