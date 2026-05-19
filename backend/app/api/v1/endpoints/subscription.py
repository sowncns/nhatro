"""Subscription Management Endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional

from app.database.session import get_db
from app.core.deps import get_tenant_context, require_owner, TenantContext
from app.database.models import Organization, Subscription, SubscriptionPlan, SaaSPayment, SaaSPaymentStatus, SaaSPaymentType
from app.core.subscription import get_plan_info, get_all_plans, SubscriptionLimits
from pydantic import BaseModel

router = APIRouter()


class SubscriptionUpgradeRequest(BaseModel):
    plan: str
    payment_method: str = "bank_transfer"


class SubscriptionResponse(BaseModel):
    current_plan: str
    max_rooms: int
    max_users: int
    features: list
    can_export: bool
    can_use_api: bool
    support_level: str
    expires_at: Optional[str] = None
    is_active: bool


@router.get("/plans")
async def list_plans():
    """Get all available subscription plans"""
    return {
        "plans": get_all_plans()
    }


@router.get("/current")
async def get_current_subscription(
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Get current subscription details"""
    org = ctx.organization
    limits = SubscriptionLimits.get_limits(org.subscription_plan)

    # Get active subscription
    sub_result = await db.execute(
        select(Subscription).where(
            Subscription.organization_id == org.id,
            Subscription.is_active == True
        ).order_by(Subscription.created_at.desc()).limit(1)
    )
    subscription = sub_result.scalar_one_or_none()

    # Get current room count
    from app.database.models import Room
    from sqlalchemy import func
    room_count_result = await db.execute(
        select(func.count()).select_from(Room).where(
            Room.organization_id == org.id
        )
    )
    current_rooms = room_count_result.scalar() or 0

    return {
        "current_plan": org.subscription_plan.value,
        "max_rooms": limits["max_rooms"],
        "current_rooms": current_rooms,
        "max_users": limits["max_users"],
        "features": limits["features"],
        "can_export": limits["can_export"],
        "can_use_api": limits["can_use_api"],
        "support_level": limits["support_level"],
        "expires_at": subscription.expires_at.isoformat() if subscription and subscription.expires_at else None,
        "is_active": subscription.is_active if subscription else True,
        "room_usage_percent": int((current_rooms / limits["max_rooms"]) * 100) if limits["max_rooms"] < 999999 else 0,
    }


@router.post("/upgrade")
async def upgrade_subscription(
    data: SubscriptionUpgradeRequest,
    ctx: TenantContext = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Upgrade subscription plan"""
    org = ctx.organization

    # Validate plan
    try:
        new_plan = SubscriptionPlan(data.plan)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan")

    # Check if downgrade
    plan_order = {
        SubscriptionPlan.FREE: 0,
        SubscriptionPlan.STARTER: 1,
        SubscriptionPlan.BASIC: 2,
        SubscriptionPlan.PRO: 3,
        SubscriptionPlan.SCALE: 4,
    }

    current_order = plan_order.get(org.subscription_plan, 0)
    new_order = plan_order.get(new_plan, 0)

    if new_order < current_order:
        raise HTTPException(
            status_code=400,
            detail="Không thể hạ cấp gói. Vui lòng liên hệ support."
        )

    if new_order == current_order:
        raise HTTPException(status_code=400, detail="Bạn đang sử dụng gói này")

    # Get plan info
    plan_info = get_plan_info(new_plan)
    price = plan_info["price"]

    # Create payment record
    import uuid
    order_code = int(datetime.now().timestamp())  # Unique order code
    payment = SaaSPayment(
        organization_id=org.id,
        user_id=ctx.user.id,
        payment_type=SaaSPaymentType.PLAN,
        status=SaaSPaymentStatus.PENDING,
        plan=new_plan,
        amount=price,
        provider="payos" if data.payment_method == "payos" else "manual",
        reference_number=f"SUB{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}",
        metadata_json={
            "old_plan": org.subscription_plan.value,
            "new_plan": new_plan.value,
            "payment_method": data.payment_method,
            "order_code": order_code,
        }
    )
    db.add(payment)
    await db.flush()

    # If PayOS payment method, create payment link
    if data.payment_method == "payos":
        from app.services.payos_service import payos_service
        from app.core.config import settings

        # Create PayOS payment link
        payos_result = payos_service.create_payment_link(
            order_code=order_code,
            amount=price,
            description=f"Nâng cấp gói {new_plan.value.upper()} - {org.name}",
            return_url=f"{settings.FRONTEND_URL}/subscription?payment=success",
            cancel_url=f"{settings.FRONTEND_URL}/subscription?payment=cancel",
            buyer_name=ctx.user.full_name,
            buyer_email=ctx.user.email,
        )

        print(f"PayOS result: {payos_result}")  # Debug log

        if payos_result["success"]:
            # Update payment with PayOS info
            payment.metadata_json["payos_data"] = payos_result["data"]
            await db.commit()

            # Generate QR code URL from checkout URL if not provided
            qr_code_url = payos_result.get("qr_code")
            print(f"QR from PayOS: {qr_code_url}")  # Debug log

            if not qr_code_url and payos_result.get("payment_url"):
                # PayOS QR code can be generated from payment URL
                qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={payos_result['payment_url']}"
                print(f"Generated QR: {qr_code_url}")  # Debug log

            response_data = {
                "payment_id": payment.id,
                "reference_number": payment.reference_number,
                "amount": price,
                "plan": new_plan.value,
                "status": "pending",
                "payment_method": "payos",
                "payment_url": payos_result["payment_url"],
                "qr_code": qr_code_url,
                "checkout_url": payos_result["payment_url"],  # For compatibility
            }
            print(f"Returning response: {response_data}")  # Debug log
            return response_data
        else:
            # PayOS failed, fallback to manual
            print(f"PayOS FAILED! Error: {payos_result.get('error')}")  # Debug log
            payment.provider = "manual"
            payment.metadata_json["payos_error"] = payos_result.get("error")
            await db.commit()

    # Manual payment (bank transfer)
    payment_info = {
        "payment_id": payment.id,
        "reference_number": payment.reference_number,
        "amount": price,
        "plan": new_plan.value,
        "status": "pending",
        "payment_method": "bank_transfer",
        "instructions": {
            "bank_name": org.bank_name or "Vietcombank",
            "account_number": org.bank_account or "1234567890",
            "account_name": org.bank_account_name or "CONG TY NHATRO",
            "content": f"THANHTOAN {payment.reference_number}",
            "note": "Vui lòng chuyển khoản và gửi ảnh chứng từ để được kích hoạt gói ngay lập tức."
        }
    }

    await db.commit()

    return payment_info


@router.post("/activate/{payment_id}")
async def activate_subscription(
    payment_id: str,
    ctx: TenantContext = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Activate subscription after payment (admin only in production)"""
    # Get payment
    payment_result = await db.execute(
        select(SaaSPayment).where(
            SaaSPayment.id == payment_id,
            SaaSPayment.organization_id == ctx.organization_id
        )
    )
    payment = payment_result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status == SaaSPaymentStatus.PAID:
        raise HTTPException(status_code=400, detail="Payment already processed")

    # Update payment status
    payment.status = SaaSPaymentStatus.PAID
    payment.paid_at = datetime.utcnow()

    # Update organization plan
    org = ctx.organization
    org.subscription_plan = payment.plan

    # Create/update subscription
    expires_at = datetime.utcnow() + timedelta(days=30)  # 1 month

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
        "success": True,
        "message": f"Đã kích hoạt gói {payment.plan.value}",
        "plan": payment.plan.value,
        "expires_at": expires_at.isoformat(),
    }


@router.get("/usage")
async def get_usage_stats(
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Get current usage statistics"""
    from app.database.models import Room, Contract, Invoice, OrganizationMember
    from sqlalchemy import func

    org = ctx.organization
    limits = SubscriptionLimits.get_limits(org.subscription_plan)

    # Count rooms
    room_count = await db.execute(
        select(func.count()).select_from(Room).where(
            Room.organization_id == org.id
        )
    )
    current_rooms = room_count.scalar() or 0

    # Count active contracts
    contract_count = await db.execute(
        select(func.count()).select_from(Contract).where(
            Contract.organization_id == org.id,
            Contract.status == "ACTIVE"
        )
    )
    active_contracts = contract_count.scalar() or 0

    # Count invoices this month
    now = datetime.now()
    invoice_count = await db.execute(
        select(func.count()).select_from(Invoice).where(
            Invoice.organization_id == org.id,
            Invoice.billing_month == now.month,
            Invoice.billing_year == now.year
        )
    )
    monthly_invoices = invoice_count.scalar() or 0

    # Count users
    user_count = await db.execute(
        select(func.count()).select_from(OrganizationMember).where(
            OrganizationMember.organization_id == org.id
        )
    )
    current_users = user_count.scalar() or 0

    return {
        "plan": org.subscription_plan.value,
        "rooms": {
            "current": current_rooms,
            "max": limits["max_rooms"],
            "usage_percent": int((current_rooms / limits["max_rooms"]) * 100) if limits["max_rooms"] < 999999 else 0,
        },
        "users": {
            "current": current_users + 1,  # +1 for owner
            "max": limits["max_users"],
            "usage_percent": int(((current_users + 1) / limits["max_users"]) * 100) if limits["max_users"] < 999999 else 0,
        },
        "active_contracts": active_contracts,
        "monthly_invoices": monthly_invoices,
    }


@router.get("/payment-history")
async def get_payment_history(
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Get subscription payment history"""
    result = await db.execute(
        select(SaaSPayment).where(
            SaaSPayment.organization_id == ctx.organization_id,
            SaaSPayment.payment_type == SaaSPaymentType.PLAN
        ).order_by(SaaSPayment.created_at.desc()).limit(20)
    )
    payments = result.scalars().all()

    return {
        "payments": [
            {
                "id": p.id,
                "reference_number": p.reference_number,
                "plan": p.plan.value if p.plan else None,
                "amount": p.amount,
                "status": p.status.value,
                "created_at": p.created_at.isoformat(),
                "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            }
            for p in payments
        ]
    }
