"""Background Tasks Package"""
from app.tasks.invoice_tasks import (
    auto_generate_monthly_invoices,
    check_overdue_invoices,
    generate_invoice_for_room,
    bulk_generate_invoices,
)
from app.tasks.contract_tasks import (
    check_expiring_contracts,
    auto_expire_contracts,
    check_deposit_returns,
)
from app.tasks.notification_tasks import (
    send_payment_reminders,
    cleanup_old_notifications,
    send_invoice_created_notification,
    send_payment_received_notification,
    send_bulk_notifications,
)

__all__ = [
    # Invoice tasks
    "auto_generate_monthly_invoices",
    "check_overdue_invoices",
    "generate_invoice_for_room",
    "bulk_generate_invoices",
    # Contract tasks
    "check_expiring_contracts",
    "auto_expire_contracts",
    "check_deposit_returns",
    # Notification tasks
    "send_payment_reminders",
    "cleanup_old_notifications",
    "send_invoice_created_notification",
    "send_payment_received_notification",
    "send_bulk_notifications",
]
