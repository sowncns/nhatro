"""Invalidation Helper - Coordinates Cache Invalidation across multiple modules"""
import logging
from typing import Optional
from app.services.cache_service import CacheService

logger = logging.getLogger("app.invalidate_helper")


class InvalidateHelper:
    @classmethod
    async def invalidate_room(cls, org_id: str, room_id: Optional[str] = None) -> None:
        """
        Invalidates room list, dashboard stats, and specific room detail (or all room details).
        Triggered on CREATE / UPDATE / DELETE of rooms.
        """
        logger.info(f"Triggering invalidation for Room. Org='{org_id}', RoomId='{room_id}'")
        await CacheService.invalidate(f"rooms:list:{org_id}")
        await CacheService.invalidate(f"dashboard:")
        
        if room_id:
            await CacheService.invalidate(f"rooms:detail:{org_id}:{room_id}")
        else:
            await CacheService.invalidate(f"rooms:detail:{org_id}")

    @classmethod
    async def invalidate_tenant(cls, org_id: str, tenant_id: Optional[str] = None) -> None:
        """
        Invalidates tenant list, dashboard stats, room detail (due to occupant updates), and tenant detail.
        Triggered on CREATE / UPDATE / DELETE of tenants.
        """
        logger.info(f"Triggering invalidation for Tenant. Org='{org_id}', TenantId='{tenant_id}'")
        await CacheService.invalidate(f"tenants:list:{org_id}")
        await CacheService.invalidate(f"dashboard:")
        await CacheService.invalidate(f"rooms:detail:{org_id}")
        
        if tenant_id:
            await CacheService.invalidate(f"tenants:detail:{org_id}:{tenant_id}")
        else:
            await CacheService.invalidate(f"tenants:detail:{org_id}")

    @classmethod
    async def invalidate_invoice(cls, org_id: str, invoice_id: Optional[str] = None) -> None:
        """
        Invalidates invoice list, dashboard stats, room detail, and specific invoice detail.
        Triggered on CREATE / UPDATE / DELETE / PAY of invoices.
        """
        logger.info(f"Triggering invalidation for Invoice. Org='{org_id}', InvoiceId='{invoice_id}'")
        await CacheService.invalidate(f"invoices:list:{org_id}")
        await CacheService.invalidate(f"dashboard:")
        await CacheService.invalidate(f"rooms:detail:{org_id}")
        
        if invoice_id:
            await CacheService.invalidate(f"invoices:detail:{org_id}:{invoice_id}")
        else:
            await CacheService.invalidate(f"invoices:detail:{org_id}")

    @classmethod
    async def invalidate_utility(cls, org_id: str, reading_id: Optional[str] = None) -> None:
        """
        Invalidates meter readings list, invoice list (as readings affect invoices), and specific reading detail.
        Triggered on CREATE / UPDATE / DELETE of meter readings.
        """
        logger.info(f"Triggering invalidation for Utility/MeterReading. Org='{org_id}', ReadingId='{reading_id}'")
        await CacheService.invalidate(f"mr:list:{org_id}")
        await CacheService.invalidate(f"invoices:list:{org_id}")
        
        if reading_id:
            await CacheService.invalidate(f"mr:detail:{org_id}:{reading_id}")
        else:
            await CacheService.invalidate(f"mr:detail:{org_id}")

    @classmethod
    async def invalidate_contract(cls, org_id: str, contract_id: Optional[str] = None) -> None:
        """
        Invalidates contract list, room detail, tenant list, dashboard, and contract detail.
        Triggered on CREATE / UPDATE / TERMINATE / CANCEL of contracts.
        """
        logger.info(f"Triggering invalidation for Contract. Org='{org_id}', ContractId='{contract_id}'")
        await CacheService.invalidate(f"contracts:list:{org_id}")
        await CacheService.invalidate(f"rooms:detail:{org_id}")
        await CacheService.invalidate(f"rooms:list:{org_id}")
        await CacheService.invalidate(f"tenants:list:{org_id}")
        await CacheService.invalidate(f"dashboard:")
        
        if contract_id:
            await CacheService.invalidate(f"contracts:detail:{org_id}:{contract_id}")
        else:
            await CacheService.invalidate(f"contracts:detail:{org_id}")
