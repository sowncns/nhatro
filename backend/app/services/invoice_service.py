"""Invoice Service - Auto-generate invoices with QR banking"""
import qrcode
import io
import base64
from datetime import date, datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException

from app.models.models import Invoice, Room, Contract, MeterReading, Organization
from app.schemas.schemas import InvoiceCreate, InvoiceResponse


class InvoiceService:
    def __init__(self, db: AsyncSession, organization_id: str):
        self.db = db
        self.organization_id = organization_id

    async def generate_invoice_number(self) -> str:
        count = await self.db.execute(
            select(func.count()).select_from(Invoice).where(
                Invoice.organization_id == self.organization_id
            )
        )
        num = (count.scalar_one() or 0) + 1
        now = datetime.now()
        return f"HD{now.year}{now.month:02d}{num:04d}"

    async def auto_generate_for_room(
        self,
        room_id: str,
        billing_month: int,
        billing_year: int,
    ) -> InvoiceResponse:
        """Auto-generate invoice from meter readings and contract"""
        # Get room
        room_result = await self.db.execute(
            select(Room).where(
                Room.id == room_id,
                Room.organization_id == self.organization_id,
            )
        )
        room = room_result.scalar_one_or_none()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        # Get active contract
        contract_result = await self.db.execute(
            select(Contract).where(
                Contract.room_id == room_id,
                Contract.organization_id == self.organization_id,
                Contract.status == "active",
            )
        )
        contract = contract_result.scalar_one_or_none()

        # Get meter reading
        meter_result = await self.db.execute(
            select(MeterReading).where(
                MeterReading.room_id == room_id,
                MeterReading.organization_id == self.organization_id,
                MeterReading.reading_month == billing_month,
                MeterReading.reading_year == billing_year,
            )
        )
        meter = meter_result.scalar_one_or_none()

        rent_amount = contract.monthly_rent if contract else room.base_price
        electricity_amount = 0
        water_amount = 0

        if meter:
            electricity_amount = int((meter.electricity_usage or 0) * room.electricity_price)
            water_amount = int((meter.water_usage or 0) * room.water_price)

        total = (
            rent_amount
            + electricity_amount
            + water_amount
            + room.internet_fee
            + room.parking_fee
        )

        due_date = date(billing_year, billing_month, contract.payment_due_day if contract else 5)

        invoice_data = InvoiceCreate(
            room_id=room_id,
            billing_month=billing_month,
            billing_year=billing_year,
            rent_amount=rent_amount,
            electricity_amount=electricity_amount,
            water_amount=water_amount,
            internet_amount=room.internet_fee,
            parking_amount=room.parking_fee,
            due_date=due_date,
        )
        return await self.create_invoice(invoice_data, contract_id=contract.id if contract else None)

    async def create_invoice(
        self,
        data: InvoiceCreate,
        contract_id: Optional[str] = None,
    ) -> InvoiceResponse:
        # Check for duplicate
        existing = await self.db.execute(
            select(Invoice).where(
                Invoice.room_id == data.room_id,
                Invoice.organization_id == self.organization_id,
                Invoice.billing_month == data.billing_month,
                Invoice.billing_year == data.billing_year,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Invoice already exists for this period")

        total = (
            data.rent_amount
            + data.electricity_amount
            + data.water_amount
            + data.internet_amount
            + data.parking_amount
            + data.other_amount
            - data.discount_amount
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
            other_amount=data.other_amount,
            discount_amount=data.discount_amount,
            total_amount=total,
            status="sent",
            notes=data.notes,
        )

        # Generate QR code for banking
        qr_data = await self._generate_banking_qr(invoice)
        invoice.qr_code_url = qr_data

        self.db.add(invoice)
        await self.db.flush()
        await self.db.refresh(invoice)
        return InvoiceResponse.model_validate(invoice)

    async def _generate_banking_qr(self, invoice: Invoice) -> str:
        """Generate VietQR banking QR code"""
        # Get org bank info
        org_result = await self.db.execute(
            select(Organization).where(Organization.id == self.organization_id)
        )
        org = org_result.scalar_one_or_none()

        if not org or not org.bank_account:
            return ""

        # VietQR format
        bank_map = {
            "Vietcombank": "970436",
            "BIDV": "970418",
            "Vietinbank": "970415",
            "Techcombank": "970407",
            "MB Bank": "970422",
            "TPBank": "970423",
            "ACB": "970416",
            "VPBank": "970432",
        }

        bank_bin = bank_map.get(org.bank_name or "", "970436")
        amount = invoice.total_amount
        description = f"Thanh toan {invoice.invoice_number}"

        qr_string = (
            f"https://img.vietqr.io/image/{bank_bin}-{org.bank_account}"
            f"-compact2.png?amount={amount}&addInfo={description}"
            f"&accountName={org.bank_account_name or ''}"
        )

        return qr_string

    async def record_payment(
        self,
        invoice_id: str,
        amount: int,
        payment_method: str = "cash",
        reference_number: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> InvoiceResponse:
        from app.models.models import Payment
        from datetime import timezone

        invoice_result = await self.db.execute(
            select(Invoice).where(
                Invoice.id == invoice_id,
                Invoice.organization_id == self.organization_id,
            )
        )
        invoice = invoice_result.scalar_one_or_none()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        payment = Payment(
            organization_id=self.organization_id,
            invoice_id=invoice_id,
            amount=amount,
            payment_method=payment_method,
            reference_number=reference_number,
            notes=notes,
        )
        self.db.add(payment)

        invoice.paid_amount += amount
        if invoice.paid_amount >= invoice.total_amount:
            invoice.status = "paid"
            invoice.paid_at = datetime.now(timezone.utc)
        elif invoice.paid_amount > 0:
            invoice.status = "sent"  # partial payment

        await self.db.flush()
        await self.db.refresh(invoice)
        return InvoiceResponse.model_validate(invoice)
