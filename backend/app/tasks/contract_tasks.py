"""Celery Tasks for Contract Operations"""
import logging
from datetime import datetime, date, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.celery_app import celery_app
from app.core.config import settings
from app.database.models import (
    Organization, Contract, ContractStatus, Notification, NotificationType, User
)

logger = logging.getLogger(__name__)

# Create async engine for Celery tasks
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@celery_app.task(name="app.tasks.contract_tasks.check_expiring_contracts")
def check_expiring_contracts():
    """
    Check contracts expiring soon and send notifications
    Runs daily
    """
    import asyncio
    return asyncio.run(_check_expiring_contracts_async())


async def _check_expiring_contracts_async():
    """Async implementation"""
    logger.info("🔍 Checking expiring contracts...")

    today = date.today()
    warning_days = [30, 15, 7, 3, 1]  # Days before expiry to send warnings
    notifications_sent = 0

    async with async_session_maker() as db:
        for days in warning_days:
            expiry_date = today + timedelta(days=days)

            # Find contracts expiring on this date
            result = await db.execute(
                select(Contract).where(
                    and_(
                        Contract.status == ContractStatus.ACTIVE,
                        Contract.end_date == expiry_date,
                        Contract.is_archived == False,
                    )
                )
            )
            contracts = result.scalars().all()

            logger.info(f"📋 Found {len(contracts)} contracts expiring in {days} days")

            for contract in contracts:
                try:
                    # Get organization owner
                    org_result = await db.execute(
                        select(Organization).where(Organization.id == contract.organization_id)
                    )
                    org = org_result.scalar_one_or_none()
                    if not org:
                        continue

                    # Create notification
                    notification = Notification(
                        organization_id=contract.organization_id,
                        user_id=org.owner_id,
                        type=NotificationType.CONTRACT_EXPIRY,
                        title=f"Hợp đồng sắp hết hạn ({days} ngày)",
                        message=f"Hợp đồng {contract.contract_number} sẽ hết hạn vào {contract.end_date.strftime('%d/%m/%Y')}. Vui lòng gia hạn hoặc thanh lý hợp đồng.",
                        data={
                            "contract_id": contract.id,
                            "contract_number": contract.contract_number,
                            "end_date": contract.end_date.isoformat(),
                            "days_remaining": days,
                        },
                    )
                    db.add(notification)
                    notifications_sent += 1

                    logger.info(f"✅ Notification sent for contract {contract.contract_number}")

                except Exception as e:
                    logger.error(f"❌ Error processing contract {contract.contract_number}: {e}")

        await db.commit()

    logger.info(f"✅ Sent {notifications_sent} expiry notifications")
    return {"notifications_sent": notifications_sent}


@celery_app.task(name="app.tasks.contract_tasks.auto_expire_contracts")
def auto_expire_contracts():
    """
    Auto-expire contracts that have passed their end date
    Runs daily
    """
    import asyncio
    return asyncio.run(_auto_expire_contracts_async())


async def _auto_expire_contracts_async():
    """Async implementation"""
    logger.info("🔍 Checking contracts to auto-expire...")

    today = date.today()
    expired_count = 0

    async with async_session_maker() as db:
        # Find active contracts past their end date
        result = await db.execute(
            select(Contract).where(
                and_(
                    Contract.status == ContractStatus.ACTIVE,
                    Contract.end_date < today,
                    Contract.is_archived == False,
                )
            )
        )
        contracts = result.scalars().all()

        logger.info(f"📋 Found {len(contracts)} contracts to expire")

        for contract in contracts:
            try:
                # Update contract status
                contract.status = ContractStatus.EXPIRED
                contract.actual_end_date = contract.end_date

                # Update room status to AVAILABLE
                from app.database.models import Room, RoomStatus
                room_result = await db.execute(
                    select(Room).where(Room.id == contract.room_id)
                )
                room = room_result.scalar_one_or_none()
                if room:
                    room.status = RoomStatus.AVAILABLE

                # Create notification
                org_result = await db.execute(
                    select(Organization).where(Organization.id == contract.organization_id)
                )
                org = org_result.scalar_one_or_none()
                if org:
                    notification = Notification(
                        organization_id=contract.organization_id,
                        user_id=org.owner_id,
                        type=NotificationType.CONTRACT_EXPIRY,
                        title="Hợp đồng đã hết hạn",
                        message=f"Hợp đồng {contract.contract_number} đã hết hạn và được chuyển sang trạng thái EXPIRED.",
                        data={
                            "contract_id": contract.id,
                            "contract_number": contract.contract_number,
                            "end_date": contract.end_date.isoformat(),
                        },
                    )
                    db.add(notification)

                expired_count += 1
                logger.info(f"✅ Expired contract {contract.contract_number}")

            except Exception as e:
                logger.error(f"❌ Error expiring contract {contract.contract_number}: {e}")

        await db.commit()

    logger.info(f"✅ Auto-expired {expired_count} contracts")
    return {"expired_count": expired_count}


@celery_app.task(name="app.tasks.contract_tasks.check_deposit_returns")
def check_deposit_returns():
    """
    Check contracts that need deposit return processing
    """
    import asyncio
    return asyncio.run(_check_deposit_returns_async())


async def _check_deposit_returns_async():
    """Async implementation"""
    logger.info("🔍 Checking contracts needing deposit returns...")

    notifications_sent = 0

    async with async_session_maker() as db:
        # Find ended/terminated contracts with unreturned deposits
        result = await db.execute(
            select(Contract).where(
                and_(
                    Contract.status.in_([ContractStatus.ENDED, ContractStatus.TERMINATED]),
                    Contract.deposit_paid == True,
                    Contract.deposit_returned == False,
                    Contract.is_archived == False,
                )
            )
        )
        contracts = result.scalars().all()

        logger.info(f"📋 Found {len(contracts)} contracts with unreturned deposits")

        for contract in contracts:
            try:
                # Get organization owner
                org_result = await db.execute(
                    select(Organization).where(Organization.id == contract.organization_id)
                )
                org = org_result.scalar_one_or_none()
                if not org:
                    continue

                # Create notification
                notification = Notification(
                    organization_id=contract.organization_id,
                    user_id=org.owner_id,
                    type=NotificationType.SYSTEM,
                    title="Cần xử lý hoàn trả tiền cọc",
                    message=f"Hợp đồng {contract.contract_number} đã kết thúc nhưng chưa hoàn trả tiền cọc. Vui lòng xử lý.",
                    data={
                        "contract_id": contract.id,
                        "contract_number": contract.contract_number,
                        "deposit_amount": contract.deposit_amount,
                    },
                )
                db.add(notification)
                notifications_sent += 1

            except Exception as e:
                logger.error(f"❌ Error processing contract {contract.contract_number}: {e}")

        await db.commit()

    logger.info(f"✅ Sent {notifications_sent} deposit return reminders")
    return {"notifications_sent": notifications_sent}
