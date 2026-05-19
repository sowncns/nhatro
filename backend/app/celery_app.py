"""Celery Configuration for Background Tasks"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Initialize Celery
celery_app = Celery(
    "nhatro_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.invoice_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.contract_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,  # 1 hour
)

# Periodic tasks schedule
celery_app.conf.beat_schedule = {
    # Auto-generate invoices on 1st of each month at 00:00
    "auto-generate-monthly-invoices": {
        "task": "app.tasks.invoice_tasks.auto_generate_monthly_invoices",
        "schedule": crontab(hour=0, minute=0, day_of_month=1),
    },
    # Check overdue invoices daily at 01:00
    "check-overdue-invoices": {
        "task": "app.tasks.invoice_tasks.check_overdue_invoices",
        "schedule": crontab(hour=1, minute=0),
    },
    # Send payment reminders daily at 09:00
    "send-payment-reminders": {
        "task": "app.tasks.notification_tasks.send_payment_reminders",
        "schedule": crontab(hour=9, minute=0),
    },
    # Check expiring contracts daily at 10:00
    "check-expiring-contracts": {
        "task": "app.tasks.contract_tasks.check_expiring_contracts",
        "schedule": crontab(hour=10, minute=0),
    },
    # Auto-expire contracts daily at 02:00
    "auto-expire-contracts": {
        "task": "app.tasks.contract_tasks.auto_expire_contracts",
        "schedule": crontab(hour=2, minute=0),
    },
    # Clean up old notifications weekly on Sunday at 03:00
    "cleanup-old-notifications": {
        "task": "app.tasks.notification_tasks.cleanup_old_notifications",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),
    },
}

# Task routes
celery_app.conf.task_routes = {
    "app.tasks.invoice_tasks.*": {"queue": "invoices"},
    "app.tasks.notification_tasks.*": {"queue": "notifications"},
    "app.tasks.contract_tasks.*": {"queue": "contracts"},
}
