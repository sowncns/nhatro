"""Subscription Middleware - Check plan limits and permissions"""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database.models import Organization, SubscriptionPlan, Room
from app.core.config import settings


class SubscriptionLimits:
    """Define limits for each subscription plan"""

    LIMITS = {
        SubscriptionPlan.FREE: {
            "max_rooms": 10,
            "max_users": 1,
            "max_devices": 1,
            "features": ["basic_invoicing", "basic_reports"],
            "can_export": False,
            "can_use_api": False,
            "support_level": "community",
        },
        SubscriptionPlan.STARTER: {
            "max_rooms": 30,
            "max_users": 2,
            "max_devices": 2,
            "features": ["basic_invoicing", "basic_reports", "email_notifications"],
            "can_export": True,
            "can_use_api": False,
            "support_level": "email",
        },
        SubscriptionPlan.BASIC: {
            "max_rooms": 50,
            "max_users": 3,
            "max_devices": 3,
            "features": ["basic_invoicing", "advanced_reports", "email_notifications", "sms_notifications"],
            "can_export": True,
            "can_use_api": False,
            "support_level": "email",
        },
        SubscriptionPlan.PRO: {
            "max_rooms": 200,
            "max_users": 10,
            "max_devices": 5,
            "features": ["basic_invoicing", "advanced_reports", "email_notifications", "sms_notifications", "auto_invoice", "payment_gateway"],
            "can_export": True,
            "can_use_api": True,
            "support_level": "priority",
        },
        SubscriptionPlan.SCALE: {
            "max_rooms": 999999,  # Unlimited
            "max_users": 999999,  # Unlimited
            "max_devices": 999999,  # Unlimited
            "features": ["all"],
            "can_export": True,
            "can_use_api": True,
            "support_level": "dedicated",
        },
    }

    @classmethod
    def get_limits(cls, plan: SubscriptionPlan) -> dict:
        """Get limits for a specific plan"""
        return cls.LIMITS.get(plan, cls.LIMITS[SubscriptionPlan.FREE])

    @classmethod
    def has_feature(cls, plan: SubscriptionPlan, feature: str) -> bool:
        """Check if plan has a specific feature"""
        limits = cls.get_limits(plan)
        features = limits.get("features", [])
        return "all" in features or feature in features


async def check_room_limit(db: AsyncSession, organization_id: str, organization: Organization = None):
    """Check if organization can create more rooms"""
    if not organization:
        result = await db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        organization = result.scalar_one_or_none()
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")

    # Get current room count
    room_count_result = await db.execute(
        select(func.count()).select_from(Room).where(
            Room.organization_id == organization_id
        )
    )
    current_rooms = room_count_result.scalar() or 0

    # Get plan limits
    limits = SubscriptionLimits.get_limits(organization.subscription_plan)
    max_rooms = limits["max_rooms"]

    if current_rooms >= max_rooms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Đã đạt giới hạn {max_rooms} phòng của gói {organization.subscription_plan.value}. Vui lòng nâng cấp gói để thêm phòng."
        )

    return True


async def check_feature_access(organization: Organization, feature: str):
    """Check if organization has access to a feature"""
    if not SubscriptionLimits.has_feature(organization.subscription_plan, feature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tính năng '{feature}' không có trong gói {organization.subscription_plan.value}. Vui lòng nâng cấp gói."
        )
    return True


async def check_export_permission(organization: Organization):
    """Check if organization can export data"""
    limits = SubscriptionLimits.get_limits(organization.subscription_plan)
    if not limits.get("can_export", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tính năng xuất dữ liệu không có trong gói {organization.subscription_plan.value}. Vui lòng nâng cấp gói."
        )
    return True


async def check_api_access(organization: Organization):
    """Check if organization can use API"""
    limits = SubscriptionLimits.get_limits(organization.subscription_plan)
    if not limits.get("can_use_api", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Quyền truy cập API không có trong gói {organization.subscription_plan.value}. Vui lòng nâng cấp gói PRO."
        )
    return True


def get_plan_info(plan: SubscriptionPlan) -> dict:
    """Get detailed information about a plan"""
    limits = SubscriptionLimits.get_limits(plan)

    # Pricing (VND per month)
    pricing = {
        SubscriptionPlan.FREE: 0,
        SubscriptionPlan.STARTER: 99000,
        SubscriptionPlan.BASIC: 199000,
        SubscriptionPlan.PRO: 499000,
        SubscriptionPlan.SCALE: 999000,
    }

    return {
        "plan": plan.value,
        "name": plan.value.title(),
        "price": pricing.get(plan, 0),
        "max_rooms": limits["max_rooms"],
        "max_users": limits["max_users"],
        "features": limits["features"],
        "can_export": limits["can_export"],
        "can_use_api": limits["can_use_api"],
        "support_level": limits["support_level"],
    }


def get_all_plans() -> list:
    """Get information about all available plans"""
    return [get_plan_info(plan) for plan in SubscriptionPlan]
