"""SaaS billing service for landlord subscriptions and paid modules."""
from datetime import datetime, timedelta, timezone
from typing import Dict, List
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    FeatureEntitlement,
    Organization,
    SaaSPayment,
    SaaSPaymentStatus,
    SaaSPaymentType,
    Subscription,
    SubscriptionPlan,
    User,
    UserRole,
)


PLAN_CATALOG: Dict[str, dict] = {
    "starter": {
        "key": "starter",
        "name": "Starter",
        "price": 199_000,
        "max_rooms": 30,
        "features": ["Quản lý phòng", "Quản lý khách thuê", "Ghi điện nước", "Xuất hóa đơn cơ bản"],
    },
    "pro": {
        "key": "pro",
        "name": "Pro",
        "price": 399_000,
        "max_rooms": 150,
        "features": ["Tạo hóa đơn tự động", "QR thanh toán", "Nhắc nợ Zalo/email", "Cảnh báo hợp đồng"],
    },
    "scale": {
        "key": "scale",
        "name": "Scale",
        "price": 799_000,
        "max_rooms": None,
        "features": ["Không giới hạn phòng", "Nhiều nhân viên", "Báo cáo nâng cao", "Hỗ trợ ưu tiên"],
    },
}

MODULE_CATALOG: Dict[str, dict] = {
    "auto_invoice": {
        "key": "auto_invoice",
        "name": "Tự động tạo hóa đơn hàng tháng",
        "description": "Hệ thống tự sinh hóa đơn theo kỳ thanh toán của từng phòng.",
        "price": 99_000,
    },
    "bank_qr": {
        "key": "bank_qr",
        "name": "QR thanh toán ngân hàng",
        "description": "Gắn VietQR riêng cho từng hóa đơn để khách thuê chuyển khoản nhanh.",
        "price": 79_000,
    },
    "zalo_email_reminder": {
        "key": "zalo_email_reminder",
        "name": "Gửi Zalo/email nhắc nợ",
        "description": "Tự gửi nhắc thanh toán trước hạn và khi quá hạn.",
        "price": 129_000,
    },
    "contract_alert": {
        "key": "contract_alert",
        "name": "Cảnh báo hợp đồng sắp hết hạn",
        "description": "Nhắc chủ trọ trước khi hợp đồng hết hạn.",
        "price": 59_000,
    },
    "advanced_reports": {
        "key": "advanced_reports",
        "name": "Báo cáo doanh thu nâng cao",
        "description": "Báo cáo lãi/lỗ, công nợ, hiệu suất từng khu trọ.",
        "price": 149_000,
    },
}


class BillingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(self, organization: Organization):
        enabled_features = await self._enabled_feature_keys(organization.id)
        payments = await self.db.execute(
            select(SaaSPayment)
            .where(SaaSPayment.organization_id == organization.id)
            .order_by(SaaSPayment.created_at.desc())
            .limit(10)
        )

        current_plan = self._plan_value(organization.subscription_plan)
        return {
            "organization_id": organization.id,
            "organization_name": organization.name,
            "current_plan": current_plan,
            "plans": [
                {**plan, "is_current": key == current_plan}
                for key, plan in PLAN_CATALOG.items()
            ],
            "modules": [
                {**module, "is_enabled": key in enabled_features}
                for key, module in MODULE_CATALOG.items()
            ],
            "recent_payments": [self._serialize_payment(item) for item in payments.scalars().all()],
        }

    async def create_checkout(self, organization: Organization, user: User, plan: str | None, feature_key: str | None, provider: str):
        if bool(plan) == bool(feature_key):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide exactly one of plan or feature_key",
            )

        if plan:
            plan_key = plan.lower()
            if plan_key not in PLAN_CATALOG:
                raise HTTPException(status_code=404, detail="Plan not found")
            amount = PLAN_CATALOG[plan_key]["price"]
            payment_type = SaaSPaymentType.PLAN
        else:
            feature_key = feature_key or ""
            if feature_key not in MODULE_CATALOG:
                raise HTTPException(status_code=404, detail="Feature module not found")
            amount = MODULE_CATALOG[feature_key]["price"]
            payment_type = SaaSPaymentType.MODULE
            plan_key = None

        reference = f"NHT-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        payment = SaaSPayment(
            organization_id=organization.id,
            user_id=user.id,
            payment_type=payment_type,
            status=SaaSPaymentStatus.PENDING,
            plan=SubscriptionPlan(plan_key) if plan_key else None,
            feature_key=feature_key,
            amount=amount,
            provider=provider,
            reference_number=reference,
            checkout_url=f"/billing/checkout/{reference}",
            metadata_json={"organization_name": organization.name},
        )
        self.db.add(payment)
        await self.db.flush()

        return {
            "payment_id": payment.id,
            "reference_number": reference,
            "amount": amount,
            "status": self._enum_value(payment.status),
            "checkout_url": payment.checkout_url,
        }

    async def mark_payment_paid(self, payment_id: str, admin_user: User | None = None, organization_id: str | None = None):
        result = await self.db.execute(select(SaaSPayment).where(SaaSPayment.id == payment_id))
        payment = result.scalar_one_or_none()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        if organization_id and payment.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Payment belongs to another organization")

        if payment.status == SaaSPaymentStatus.PAID:
            return self._serialize_payment(payment)

        payment.status = SaaSPaymentStatus.PAID
        payment.paid_at = datetime.now(timezone.utc)
        payment.approved_by = admin_user.id if admin_user else None

        org = await self.db.get(Organization, payment.organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        if payment.payment_type == SaaSPaymentType.PLAN and payment.plan:
            await self._activate_plan(org, payment)
        elif payment.payment_type == SaaSPaymentType.MODULE and payment.feature_key:
            await self._activate_feature(org, payment)

        await self.db.flush()
        return self._serialize_payment(payment)

    async def list_payments(self, status_filter: str | None = None):
        query = select(SaaSPayment).order_by(SaaSPayment.created_at.desc())
        if status_filter:
            query = query.where(SaaSPayment.status == SaaSPaymentStatus(status_filter))
        result = await self.db.execute(query.limit(100))
        return [self._serialize_payment(payment) for payment in result.scalars().all()]

    async def platform_stats(self):
        owners = await self.db.scalar(select(func.count(User.id)).where(User.role == UserRole.OWNER))
        organizations = await self.db.scalar(select(func.count(Organization.id)))
        active_subscriptions = await self.db.scalar(select(func.count(Subscription.id)).where(Subscription.is_active == True))
        paid_revenue = await self.db.scalar(
            select(func.coalesce(func.sum(SaaSPayment.amount), 0)).where(SaaSPayment.status == SaaSPaymentStatus.PAID)
        )
        pending_payments = await self.db.scalar(
            select(func.count(SaaSPayment.id)).where(SaaSPayment.status == SaaSPaymentStatus.PENDING)
        )
        return {
            "owners": owners or 0,
            "organizations": organizations or 0,
            "active_subscriptions": active_subscriptions or 0,
            "paid_revenue": paid_revenue or 0,
            "pending_payments": pending_payments or 0,
        }

    async def list_customers(self):
        result = await self.db.execute(
            select(Organization, User)
            .join(User, User.id == Organization.owner_id)
            .order_by(Organization.created_at.desc())
            .limit(100)
        )
        return [
            {
                "organization_id": org.id,
                "organization_name": org.name,
                "owner_email": owner.email,
                "owner_name": owner.full_name,
                "plan": self._plan_value(org.subscription_plan),
                "is_active": org.is_active,
                "created_at": org.created_at,
            }
            for org, owner in result.all()
        ]

    async def _activate_plan(self, organization: Organization, payment: SaaSPayment):
        organization.subscription_plan = payment.plan
        active_subscriptions = await self.db.execute(
            select(Subscription).where(
                Subscription.organization_id == organization.id,
                Subscription.is_active == True,
            )
        )
        for subscription in active_subscriptions.scalars().all():
            subscription.is_active = False

        subscription = Subscription(
            organization_id=organization.id,
            plan=payment.plan,
            price=payment.amount,
            starts_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_active=True,
        )
        self.db.add(subscription)

    async def _activate_feature(self, organization: Organization, payment: SaaSPayment):
        module = MODULE_CATALOG[payment.feature_key]
        existing = await self.db.execute(
            select(FeatureEntitlement).where(
                FeatureEntitlement.organization_id == organization.id,
                FeatureEntitlement.feature_key == payment.feature_key,
                FeatureEntitlement.is_active == True,
            )
        )
        entitlement = existing.scalar_one_or_none()
        if entitlement:
            entitlement.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
            entitlement.source_payment_id = payment.id
            return

        self.db.add(
            FeatureEntitlement(
                organization_id=organization.id,
                feature_key=payment.feature_key,
                name=module["name"],
                source_payment_id=payment.id,
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            )
        )

    async def _enabled_feature_keys(self, organization_id: str) -> List[str]:
        result = await self.db.execute(
            select(FeatureEntitlement.feature_key).where(
                FeatureEntitlement.organization_id == organization_id,
                FeatureEntitlement.is_active == True,
            )
        )
        return list(result.scalars().all())

    def _serialize_payment(self, payment: SaaSPayment):
        return {
            "id": payment.id,
            "organization_id": payment.organization_id,
            "user_id": payment.user_id,
            "payment_type": self._enum_value(payment.payment_type),
            "status": self._enum_value(payment.status),
            "plan": self._enum_value(payment.plan) if payment.plan else None,
            "feature_key": payment.feature_key,
            "amount": payment.amount,
            "provider": payment.provider,
            "reference_number": payment.reference_number,
            "checkout_url": payment.checkout_url,
            "paid_at": payment.paid_at,
            "created_at": payment.created_at,
        }

    def _enum_value(self, value):
        return getattr(value, "value", value)

    def _plan_value(self, value):
        return getattr(value, "value", value) or "free"
