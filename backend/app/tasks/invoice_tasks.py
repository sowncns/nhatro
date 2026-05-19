"""Celery Tasks for Invoice Operations"""
import logging
from datetime import datetime, date, timedelta
from typing import List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.celery_app import celery_app
from app.core.config import settings
from app.database.models import (
    Organization, Contract, ContractStatus, Invoice, InvoiceStatus, Room
)
from app.services.invoice_service_improved import ImprovedInvoiceService

logger = logging.getLogger(__name__)

# Create async engine for Celery tasks
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@celery_app.task(name="app.tasks.invoice_tasks.auto_generate_monthly_invoices")
def auto_generate_monthly_invoices():
    """
    Auto-generate invoices for all active contracts
    Runs on 1st of each month
    """
    import asyncio
    return asyncio.run(_auto_generate_monthly_invoices_async())


async def _auto_generate_monthly_invoices_async():
    """Async implementation of auto invoice generation"""
    logger.info("🚀 Starting auto invoice generation...")

    now = datetime.now()
    billing_month = now.month
    billing_year = now.year

    async with async_session_maker() as db:
        # Get all active organizations
        org_result = await db.execute(
            select(Organization).where(Organization.is_active == True)
        )
        organizations = org_result.scalars().all()

        total_generated = 0
        total_errors = 0

        for org in organizations:
            try:
                # Check if organization has auto_invoice feature enabled
                settings_dict = org.settings or {}
                if not settings_dict.get("auto_invoice_enabled", False):
                    logger.info(f"⏭️ Skipping {org.name} - auto invoice not enabled")
                    continue

                # Get all active contracts for this organization
                contract_result = await db.execute(
                    select(Contract).where(
                        and_(
                            Contract.organization_id == org.id,
                            Contract.status == ContractStatus.ACTIVE,
                            Contract.is_archived == False,
                        )
                    )
                )
                contracts = contract_result.scalars().all()

                logger.info(f"📋 Processing {len(contracts)} contracts for {org.name}")

                for contract in contracts:
                    try:
                        # Check if invoice already exists
                        existing = await db.execute(
                            select(Invoice).where(
                                and_(
                                    Invoice.room_id == contract.room_id,
                                    Invoice.billing_month == billing_month,
                                    Invoice.billing_year == billing_year,
                                    Invoice.is_archived == False,
                                )
                            )
                        )
                        if existing.scalar_one_or_none():
                            logger.debug(f"⏭️ Invoice already exists for contract {contract.contract_number}")
                            continue

                        # Generate invoice
                        service = ImprovedInvoiceService(db, org.id)
                        invoice = await service.auto_generate_for_room(
                            room_id=contract.room_id,
                            billing_month=billing_month,
                            billing_year=billing_year,
                            idempotency_key=f"auto_{org.id}_{contract.room_id}_{billing_year}{billing_month:02d}",
                        )

                        # Auto-confirm invoice if enabled
                        if settings_dict.get("auto_confirm_invoice", False):
                            invoice_obj = await db.get(Invoice, invoice.id)
                            if invoice_obj:
                                invoice_obj.status = InvoiceStatus.SENT
                                await db.flush()

                        total_generated += 1
                        logger.info(f"✅ Generated invoice {invoice.invoice_number} for contract {contract.contract_number}")

                    except Exception as e:
                        total_errors += 1
                        logger.error(f"❌ Error generating invoice for contract {contract.contract_number}: {e}")

                await db.commit()

            except Exception as e:
                logger.error(f"❌ Error processing organization {org.name}: {e}")
                total_errors += 1

    logger.info(f"✅ Auto invoice generation completed: {total_generated} generated, {total_errors} errors")
    return {"generated": total_generated, "errors": total_errors}


@celery_app.task(name="app.tasks.invoice_tasks.check_overdue_invoices")
def check_overdue_invoices():
    """
    Check and update overdue invoices
    Runs daily
    """
    import asyncio
    return asyncio.run(_check_overdue_invoices_async())


async def _check_overdue_invoices_async():
    """Async implementation of overdue check"""
    logger.info("🔍 Checking overdue invoices...")

    today = date.today()
    updated_count = 0

    async with async_session_maker() as db:
        # Find invoices that are overdue
        result = await db.execute(
            select(Invoice).where(
                and_(
                    Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.DRAFT]),
                    Invoice.due_date < today,
                    Invoice.is_archived == False,
                )
            )
        )
        overdue_invoices = result.scalars().all()

        logger.info(f"📋 Found {len(overdue_invoices)} overdue invoices")

        for invoice in overdue_invoices:
            try:
                invoice.status = InvoiceStatus.OVERDUE
                updated_count += 1
            except Exception as e:
                logger.error(f"❌ Error updating invoice {invoice.invoice_number}: {e}")

        await db.commit()

    logger.info(f"✅ Updated {updated_count} invoices to OVERDUE status")
    return {"updated": updated_count}


@celery_app.task(name="app.tasks.invoice_tasks.generate_invoice_for_room")
def generate_invoice_for_room(organization_id: str, room_id: str, billing_month: int, billing_year: int):
    """
    Generate invoice for a specific room (can be called manually)
    """
    import asyncio
    return asyncio.run(_generate_invoice_for_room_async(organization_id, room_id, billing_month, billing_year))


async def _generate_invoice_for_room_async(
    organization_id: str, room_id: str, billing_month: int, billing_year: int
):
    """Async implementation"""
    async with async_session_maker() as db:
        service = ImprovedInvoiceService(db, organization_id)
        invoice = await service.auto_generate_for_room(
            room_id=room_id,
            billing_month=billing_month,
            billing_year=billing_year,
        )
        await db.commit()

        logger.info(f"✅ Generated invoice {invoice.invoice_number}")
        return {"invoice_id": invoice.id, "invoice_number": invoice.invoice_number}


@celery_app.task(name="app.tasks.invoice_tasks.bulk_generate_invoices")
def bulk_generate_invoices(organization_id: str, room_ids: List[str], billing_month: int, billing_year: int):
    """
    Bulk generate invoices for multiple rooms
    """
    import asyncio
    return asyncio.run(_bulk_generate_invoices_async(organization_id, room_ids, billing_month, billing_year))


async def _bulk_generate_invoices_async(
    organization_id: str, room_ids: List[str], billing_month: int, billing_year: int
):
    """Async implementation of bulk generation"""
    logger.info(f"🚀 Bulk generating {len(room_ids)} invoices...")

    generated = []
    errors = []

    async with async_session_maker() as db:
        service = ImprovedInvoiceService(db, organization_id)

        for room_id in room_ids:
            try:
                invoice = await service.auto_generate_for_room(
                    room_id=room_id,
                    billing_month=billing_month,
                    billing_year=billing_year,
                )
                generated.append(invoice.invoice_number)
                logger.info(f"✅ Generated invoice {invoice.invoice_number}")
            except Exception as e:
                errors.append({"room_id": room_id, "error": str(e)})
                logger.error(f"❌ Error generating invoice for room {room_id}: {e}")

        await db.commit()

    logger.info(f"✅ Bulk generation completed: {len(generated)} generated, {len(errors)} errors")
    return {"generated": generated, "errors": errors}
