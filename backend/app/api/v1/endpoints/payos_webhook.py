"""PayOS Webhook Handler"""
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.database.session import get_db
from app.database.models import SaaSPayment, SaaSPaymentStatus, Organization, Subscription
from app.services.payos_service import payos_service

router = APIRouter()


@router.post("/payos/webhook")
async def payos_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    PayOS webhook handler
    Receives payment status updates from PayOS
    """
    try:
        # Get webhook data
        body = await request.json()

        # Get signature from header
        signature = request.headers.get("x-payos-signature", "")

        # Verify signature
        if not payos_service.verify_webhook_signature(body, signature):
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Extract payment info
        data = body.get("data", {})
        order_code = data.get("orderCode")
        status = data.get("status")  # PAID, CANCELLED, PENDING
        amount = data.get("amount")

        if not order_code:
            raise HTTPException(status_code=400, detail="Missing order_code")

        # Find payment by order_code
        result = await db.execute(
            select(SaaSPayment).where(
                SaaSPayment.metadata_json["order_code"].astext == str(order_code)
            )
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        # Update payment status based on PayOS status
        if status == "PAID":
            payment.status = SaaSPaymentStatus.PAID
            payment.paid_at = datetime.utcnow()

            # Auto-activate subscription
            org_result = await db.execute(
                select(Organization).where(Organization.id == payment.organization_id)
            )
            org = org_result.scalar_one_or_none()

            if org and payment.plan:
                # Update organization plan
                org.subscription_plan = payment.plan

                # Create/update subscription
                expires_at = datetime.utcnow() + timedelta(days=30)
                subscription = Subscription(
                    organization_id=org.id,
                    plan=payment.plan,
                    price=payment.amount,
                    starts_at=datetime.utcnow(),
                    expires_at=expires_at,
                    is_active=True,
                )
                db.add(subscription)

                # TODO: Send email notification

        elif status == "CANCELLED":
            payment.status = SaaSPaymentStatus.CANCELLED

        # Update payment metadata
        payment.metadata_json["webhook_data"] = data
        payment.metadata_json["webhook_received_at"] = datetime.utcnow().isoformat()

        await db.commit()

        return {
            "success": True,
            "message": "Webhook processed successfully"
        }

    except Exception as e:
        # Log error but return 200 to prevent PayOS retry
        print(f"PayOS webhook error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/payos/check/{order_code}")
async def check_payos_payment(
    order_code: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually check PayOS payment status
    Useful for debugging or manual verification
    """
    # Get payment info from PayOS
    result = payos_service.get_payment_info(order_code)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))

    payos_data = result["data"]
    status = payos_data.get("status")

    # Find payment in database
    db_result = await db.execute(
        select(SaaSPayment).where(
            SaaSPayment.metadata_json["order_code"].astext == str(order_code)
        )
    )
    payment = db_result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found in database")

    # Sync status if different
    if status == "PAID" and payment.status != SaaSPaymentStatus.PAID:
        payment.status = SaaSPaymentStatus.PAID
        payment.paid_at = datetime.utcnow()

        # Auto-activate subscription
        org_result = await db.execute(
            select(Organization).where(Organization.id == payment.organization_id)
        )
        org = org_result.scalar_one_or_none()

        if org and payment.plan:
            org.subscription_plan = payment.plan

            expires_at = datetime.utcnow() + timedelta(days=30)
            subscription = Subscription(
                organization_id=org.id,
                plan=payment.plan,
                price=payment.amount,
                starts_at=datetime.utcnow(),
                expires_at=expires_at,
                is_active=True,
            )
            db.add(subscription)

        await db.commit()

    return {
        "order_code": order_code,
        "payos_status": status,
        "db_status": payment.status.value,
        "synced": True,
        "payment_id": payment.id,
    }
