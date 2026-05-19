"""Improved Invoice Service - Fixed race conditions and better transaction handling"""
import qrcode
import io
import base64
import hashlib
from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException
import logging

from app.database.models import (
    Invoice, Room, Contract, MeterReading, Organization,
    InvoiceStatus, ContractStatus
)
from app.schemas.schemas import InvoiceCreate, InvoiceResponse
from app.core.config import settings

logger = logging.getLogger(__name__)


class ImprovedInvoiceService:
    """
    Improved invoice service with:
    - Fixed race condition in invoice number generation
    - Proper transaction handling
    - Better error handling
    - Idempotency support
    """

    def __init__(self, db: AsyncSession, organization_id: str):
        self.db = db
        self.organization_id = organization_id

    async def generate_invoice_number(self) -> str:
        """
        Generate unique invoice number with better collision prevention
        Uses database sequence + timestamp + hash for uniqueness
        """
        # Use database transaction to ensure atomicity
        async with self.db.begin_nested():
            # Get count with FOR UPDATE to lock
            result = await self.db.execute(
                select(func.count())
                .select_from(Invoice)
                .where(Invoice.organization_id == self.organization_id)
                .with_for_update()
            )
            count = result.scalar() or 0
            num = count + 1

            now = datetime.now()
            # Create unique hash from org_id + timestamp + count
            unique_str = f"{self.organization_id}{now.timestamp()}{num}"
            hash_suffix = hashlib.md5(unique_str.encode()).hexdigest()[:4].upper()

            invoice_number = f"HD{now.year}{now.month:02d}{num:04d}{hash_suffix}"

            # Double check uniqueness
            check = await self.db.execute(
                select(Invoice).where(Invoice.invoice_number == invoice_number)
            )
            if check.scalar_one_or_none():
                # Collision detected, add extra random suffix
                import random
                invoice_number += str(random.randint(10, 99))

            return invoice_number

    async def auto_generate_for_room(
        self,
        room_id: str,
        billing_month: int,
        billing_year: int,
        idempotency_key: Optional[str] = None,
    ) -> InvoiceResponse:
        """
        Auto-generate invoice from meter readings and contract

        Args:
            room_id: Room ID
            billing_month: Billing month (1-12)
            billing_year: Billing year
            idempotency_key: Optional key to prevent duplicate invoice creation
        """
        # Check for existing invoice (idempotency)
        if idempotency_key:
            existing = await self._check_idempotency(idempotency_key)
            if existing:
                return InvoiceResponse.model_validate(existing)

        # Start transaction
        async with self.db.begin_nested():
            # Get room with lock
            room_result = await self.db.execute(
                select(Room)
                .where(
                    Room.id == room_id,
                    Room.organization_id == self.organization_id,
                    Room.is_archived == False,
                )
                .with_for_update()
            )
            room = room_result.scalar_one_or_none()
            if not room:
                raise HTTPException(status_code=404, detail="Room not found")

            # Get active contract
            contract_result = await self.db.execute(
                select(Contract)
                .where(
                    Contract.room_id == room_id,
                    Contract.organization_id == self.organization_id,
                    Contract.status == ContractStatus.ACTIVE,
                    Contract.is_archived == False,
                )
                .order_by(Contract.created_at.desc())
                .limit(1)
            )
            contract = contract_result.scalar_one_or_none()

            # Check for duplicate invoice
            duplicate_check = await self.db.execute(
                select(Invoice).where(
                    Invoice.room_id == room_id,
                    Invoice.organization_id == self.organization_id,
                    Invoice.billing_month == billing_month,
                    Invoice.billing_year == billing_year,
                    Invoice.is_archived == False,
                )
            )
            if duplicate_check.scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail=f"Invoice for {billing_month}/{billing_year} already exists"
                )

            # Get meter reading
            meter_result = await self.db.execute(
                select(MeterReading)
                .where(
                    MeterReading.room_id == room_id,
                    MeterReading.organization_id == self.organization_id,
                    MeterReading.reading_month == billing_month,
                    MeterReading.reading_year == billing_year,
                    MeterReading.is_archived == False,
                )
                .order_by(MeterReading.recorded_at.desc())
                .limit(1)
            )
            meter = meter_result.scalar_one_or_none()

            # Calculate amounts
            rent_amount = contract.monthly_rent if contract else room.base_price
            electricity_amount = 0
            water_amount = 0

            if meter:
                electricity_amount = int(
                    (meter.electricity_usage or 0) * (room.electricity_price or 0)
                )
                water_amount = int((meter.water_usage or 0) * (room.water_price or 0))

            # Get organization settings for parking
            org_result = await self.db.execute(
                select(Organization).where(Organization.id == self.organization_id)
            )
            org = org_result.scalar_one_or_none()
            org_settings = (org.settings or {}) if org else {}
            default_parking = org_settings.get("default_parking_fee", 0) or 0

            parking_per_vehicle = room.parking_fee or default_parking
            v_count = (contract.vehicle_count if contract else 0) or 0
            parking_amount = (
                parking_per_vehicle * v_count if v_count > 0 else parking_per_vehicle
            )

            # Get old debt from last invoice
            old_debt = await self._get_old_debt(room_id)

            # Calculate total
            total = (
                (rent_amount or 0)
                + (electricity_amount or 0)
                + (water_amount or 0)
                + (room.internet_fee or 0)
                + parking_amount
                + old_debt
            )

            # Calculate due date
            import calendar
            due_day = (
                contract.payment_due_day if contract and contract.payment_due_day else 5
            )
            _, last_day = calendar.monthrange(billing_year, billing_month)
            due_date = date(billing_year, billing_month, min(due_day, last_day))

            # Create invoice
            invoice_data = InvoiceCreate(
                room_id=room_id,
                billing_month=billing_month,
                billing_year=billing_year,
                rent_amount=(rent_amount or 0),
                electricity_amount=(electricity_amount or 0),
                water_amount=(water_amount or 0),
                internet_amount=(room.internet_fee or 0),
                parking_amount=parking_amount,
                vehicle_count=v_count,
                old_debt=old_debt,
                due_date=due_date,
            )

            invoice = await self._create_invoice_internal(
                invoice_data, contract_id=contract.id if contract else None
            )

            # Store idempotency key if provided
            if idempotency_key:
                await self._store_idempotency(idempotency_key, invoice.id)

            return InvoiceResponse.model_validate(invoice)

    async def _get_old_debt(self, room_id: str) -> int:
        """Get unpaid amount from last invoice"""
        last_invoice_result = await self.db.execute(
            select(Invoice)
            .where(
                Invoice.room_id == room_id,
                Invoice.organization_id == self.organization_id,
                Invoice.is_archived == False,
            )
            .order_by(Invoice.billing_year.desc(), Invoice.billing_month.desc())
            .limit(1)
        )
        last_invoice = last_invoice_result.scalar_one_or_none()

        if last_invoice:
            unpaid = (last_invoice.total_amount or 0) - (last_invoice.paid_amount or 0)
            return max(0, unpaid)

        return 0

    async def _create_invoice_internal(
        self, data: InvoiceCreate, contract_id: Optional[str] = None
    ) -> Invoice:
        """Internal method to create invoice (assumes transaction is already started)"""
        total = (
            (data.rent_amount or 0)
            + (data.electricity_amount or 0)
            + (data.water_amount or 0)
            + (data.internet_amount or 0)
            + (data.parking_amount or 0)
            + (data.other_amount or 0)
            + (data.old_debt or 0)
            - (data.discount_amount or 0)
        )

        invoice = Invoice(
            organization_id=self.organization_id,
            room_id=data.room_id,
            contract_id=contract_id,
            invoice_number=await self.generate_invoice_number(),
            billing_month=data.billing_month,
            billing_year=data.billing_year,
            due_date=data.due_date,
            rent_amount=data.rent_amount,
            electricity_amount=data.electricity_amount,
            water_amount=data.water_amount,
            internet_amount=data.internet_amount,
            parking_amount=data.parking_amount,
            vehicle_count=data.vehicle_count,
            other_amount=data.other_amount,
            discount_amount=data.discount_amount,
            old_debt=data.old_debt,
            total_amount=total,
            status=InvoiceStatus.DRAFT,
            notes=data.notes,
        )

        # Generate QR code
        qr_data = await self._generate_banking_qr(invoice)
        invoice.qr_code_url = qr_data

        self.db.add(invoice)
        await self.db.flush()
        await self.db.refresh(invoice)
        return invoice

    async def _generate_banking_qr(self, invoice: Invoice) -> str:
        """Generate VietQR image URL for direct bank transfer"""
        org_result = await self.db.execute(
            select(Organization).where(Organization.id == invoice.organization_id)
        )
        org = org_result.scalar_one_or_none()

        if org and org.bank_name and org.bank_account:
            amount = invoice.total_amount - (invoice.paid_amount or 0)
            description = f"THANH TOAN HOA DON {invoice.invoice_number}"

            import urllib.parse

            desc_encoded = urllib.parse.quote(description)
            name_encoded = urllib.parse.quote(org.bank_account_name or "")

            return f"https://img.vietqr.io/image/{org.bank_name}-{org.bank_account}-compact2.png?amount={amount}&addInfo={desc_encoded}&accountName={name_encoded}"

        return ""

    async def _check_idempotency(self, key: str) -> Optional[Invoice]:
        """Check if invoice was already created with this idempotency key"""
        # Store idempotency keys in organization settings or separate table
        # For now, use invoice notes field with special prefix
        result = await self.db.execute(
            select(Invoice).where(
                Invoice.organization_id == self.organization_id,
                Invoice.notes.like(f"%IDEMPOTENCY:{key}%"),
            )
        )
        return result.scalar_one_or_none()

    async def _store_idempotency(self, key: str, invoice_id: str):
        """Store idempotency key"""
        # Append to invoice notes
        invoice = await self.db.get(Invoice, invoice_id)
        if invoice:
            current_notes = invoice.notes or ""
            invoice.notes = f"{current_notes}\nIDEMPOTENCY:{key}"
            await self.db.flush()

    async def record_payment(
        self,
        invoice_id: str,
        amount: int,
        payment_method: str = "CASH",
        reference_number: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> InvoiceResponse:
        """Record payment with proper transaction handling"""
        from app.database.models import Payment, PaymentMethod as PM

        async with self.db.begin_nested():
            # Get invoice with lock
            invoice_result = await self.db.execute(
                select(Invoice)
                .where(
                    Invoice.id == invoice_id,
                    Invoice.organization_id == self.organization_id,
                )
                .with_for_update()
            )
            invoice = invoice_result.scalar_one_or_none()
            if not invoice:
                raise HTTPException(status_code=404, detail="Invoice not found")

            # Validate payment amount
            remaining = invoice.total_amount - (invoice.paid_amount or 0)
            if amount > remaining:
                raise HTTPException(
                    status_code=400,
                    detail=f"Payment amount ({amount}) exceeds remaining balance ({remaining})",
                )

            # Create payment record
            payment = Payment(
                organization_id=self.organization_id,
                invoice_id=invoice_id,
                amount=amount,
                payment_method=PM[payment_method.upper()],
                reference_number=reference_number,
                notes=notes,
            )
            self.db.add(payment)

            # Update invoice
            invoice.paid_amount = (invoice.paid_amount or 0) + amount

            if invoice.paid_amount >= invoice.total_amount:
                invoice.status = InvoiceStatus.PAID
                invoice.paid_at = datetime.now(timezone.utc)
            elif invoice.paid_amount > 0:
                invoice.status = InvoiceStatus.SENT  # partial payment

            await self.db.flush()
            await self.db.refresh(invoice)

            logger.info(
                f"Payment recorded: Invoice {invoice.invoice_number}, Amount {amount}, Method {payment_method}"
            )

            return InvoiceResponse.model_validate(invoice)
