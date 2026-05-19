"""Celery Tasks for Notification Operations"""
import logging
from datetime import datetime, date, timedelta
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.celery_app import celery_app
from app.core.config import settings
from app.database.models import (
    Organization, Invoice, InvoiceStatus, Notification, NotificationType, Contract
)

logger = logging.getLogger(__name__)

# Create async engine for Celery tasks
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@celery_app.task(name="app.tasks.notification_tasks.send_payment_reminders")
def send_payment_reminders():
    """
    Send payment reminders for unpaid invoices
    Runs daily
    """
    import asyncio
    return asyncio.run(_send_payment_reminders_async())


async def _send_payment_reminders_async():
    """Async implementation"""
    logger.info("📧 Sending payment reminders...")

    today = date.today()
    reminder_days = [7, 3, 1, 0, -1, -3, -7]  # Days before/after due date
    notifications_sent = 0

    async with async_session_maker() as db:
        for days in reminder_days:
            target_date = today - timedelta(days=days)

            # Find unpaid invoices with this due date
            result = await db.execute(
                select(Invoice).where(
                    and_(
                        Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.OVERDUE]),
                        Invoice.due_date == target_date,
                        Invoice.is_archived == False,
                    )
                )
            )
            invoices = result.scalars().all()

            if not invoices:
                continue

            logger.info(f"📋 Found {len(invoices)} invoices due on {target_date}")

            for invoice in invoices:
                try:
                    # Get organization
                    org_result = await db.execute(
                        select(Organization).where(Organization.id == invoice.organization_id)
                    )
                    org = org_result.scalar_one_or_none()
                    if not org:
                        continue

                    # Determine message based on days
                    if days > 0:
                        title = f"Nhắc nhở thanh toán ({days} ngày trước hạn)"
                        message = f"Hóa đơn {invoice.invoice_number} sẽ đến hạn thanh toán vào {invoice.due_date.strftime('%d/%m/%Y')}. Số tiền: {invoice.total_amount:,} VNĐ"
                    elif days == 0:
                        title = "Hóa đơn đến hạn thanh toán hôm nay"
                        message = f"Hóa đơn {invoice.invoice_number} đến hạn thanh toán hôm nay. Số tiền: {invoice.total_amount:,} VNĐ"
                    else:
                        title = f"Hóa đơn quá hạn ({abs(days)} ngày)"
                        message = f"Hóa đơn {invoice.invoice_number} đã quá hạn {abs(days)} ngày. Vui lòng thanh toán sớm. Số tiền: {invoice.total_amount:,} VNĐ"

                    # Create notification
                    notification = Notification(
                        organization_id=invoice.organization_id,
                        user_id=org.owner_id,
                        type=NotificationType.INVOICE_DUE,
                        title=title,
                        message=message,
                        data={
                            "invoice_id": invoice.id,
                            "invoice_number": invoice.invoice_number,
                            "due_date": invoice.due_date.isoformat(),
                            "total_amount": invoice.total_amount,
                            "days_overdue": abs(days) if days < 0 else 0,
                        },
                    )
                    db.add(notification)
                    notifications_sent += 1

                    # TODO: Send email/SMS if enabled
                    # await send_email_reminder(invoice, org)
                    # await send_sms_reminder(invoice, contract)

                    logger.info(f"✅ Reminder sent for invoice {invoice.invoice_number}")

                except Exception as e:
                    logger.error(f"❌ Error sending reminder for invoice {invoice.invoice_number}: {e}")

        await db.commit()

    logger.info(f"✅ Sent {notifications_sent} payment reminders")
    return {"notifications_sent": notifications_sent}


@celery_app.task(name="app.tasks.notification_tasks.cleanup_old_notifications")
def cleanup_old_notifications():
    """
    Clean up old read notifications (older than 30 days)
    Runs weekly
    """
    import asyncio
    return asyncio.run(_cleanup_old_notifications_async())


async def _cleanup_old_notifications_async():
    """Async implementation"""
    logger.info("🧹 Cleaning up old notifications...")

    cutoff_date = datetime.now() - timedelta(days=30)
    deleted_count = 0

    async with async_session_maker() as db:
        # Delete old read notifications
        result = await db.execute(
            delete(Notification).where(
                and_(
                    Notification.is_read == True,
                    Notification.created_at < cutoff_date,
                )
            )
        )
        deleted_count = result.rowcount
        await db.commit()

    logger.info(f"✅ Deleted {deleted_count} old notifications")
    return {"deleted_count": deleted_count}


@celery_app.task(name="app.tasks.notification_tasks.send_invoice_created_notification")
def send_invoice_created_notification(invoice_id: str, organization_id: str):
    """
    Send notification when new invoice is created
    """
    import asyncio
    return asyncio.run(_send_invoice_created_notification_async(invoice_id, organization_id))


async def _send_invoice_created_notification_async(invoice_id: str, organization_id: str):
    """Async implementation"""
    async with async_session_maker() as db:
        # Get invoice
        invoice = await db.get(Invoice, invoice_id)
        if not invoice:
            logger.error(f"❌ Invoice {invoice_id} not found")
            return {"success": False}

        # Get organization
        org = await db.get(Organization, organization_id)
        if not org:
            logger.error(f"❌ Organization {organization_id} not found")
            return {"success": False}

        # Create notification
        notification = Notification(
            organization_id=organization_id,
            user_id=org.owner_id,
            type=NotificationType.SYSTEM,
            title="Hóa đơn mới được tạo",
            message=f"Hóa đơn {invoice.invoice_number} đã được tạo. Số tiền: {invoice.total_amount:,} VNĐ",
            data={
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "total_amount": invoice.total_amount,
            },
        )
        db.add(notification)
        await db.commit()

        logger.info(f"✅ Notification sent for invoice {invoice.invoice_number}")
        return {"success": True}


@celery_app.task(name="app.tasks.notification_tasks.send_payment_received_notification")
def send_payment_received_notification(invoice_id: str, amount: int, organization_id: str):
    """
    Send notification when payment is received
    """
    import asyncio
    return asyncio.run(_send_payment_received_notification_async(invoice_id, amount, organization_id))


async def _send_payment_received_notification_async(invoice_id: str, amount: int, organization_id: str):
    """Async implementation"""
    async with async_session_maker() as db:
        # Get invoice
        invoice = await db.get(Invoice, invoice_id)
        if not invoice:
            return {"success": False}

        # Get organization
        org = await db.get(Organization, organization_id)
        if not org:
            return {"success": False}

        # Create notification
        notification = Notification(
            organization_id=organization_id,
            user_id=org.owner_id,
            type=NotificationType.PAYMENT_RECEIVED,
            title="Đã nhận thanh toán",
            message=f"Đã nhận thanh toán {amount:,} VNĐ cho hóa đơn {invoice.invoice_number}",
            data={
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "amount": amount,
                "remaining": invoice.total_amount - invoice.paid_amount,
            },
        )
        db.add(notification)
        await db.commit()

        logger.info(f"✅ Payment notification sent for invoice {invoice.invoice_number}")
        return {"success": True}


@celery_app.task(name="app.tasks.notification_tasks.send_bulk_notifications")
def send_bulk_notifications(organization_id: str, user_ids: list, title: str, message: str, notification_type: str = "system"):
    """
    Send bulk notifications to multiple users
    """
    import asyncio
    return asyncio.run(_send_bulk_notifications_async(organization_id, user_ids, title, message, notification_type))


async def _send_bulk_notifications_async(
    organization_id: str, user_ids: list, title: str, message: str, notification_type: str
):
    """Async implementation"""
    async with async_session_maker() as db:
        notifications = []
        for user_id in user_ids:
            notification = Notification(
                organization_id=organization_id,
                user_id=user_id,
                type=NotificationType[notification_type.upper()],
                title=title,
                message=message,
            )
            notifications.append(notification)
            db.add(notification)

        await db.commit()

        logger.info(f"✅ Sent {len(notifications)} bulk notifications")
        return {"sent": len(notifications)}
