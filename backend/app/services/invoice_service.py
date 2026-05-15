"""Invoice Service - Auto-generate invoices with QR banking"""
import qrcode
import io
import base64
import time
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
        result = await self.db.execute(
            select(func.count()).select_from(Invoice).where(
                Invoice.organization_id == self.organization_id
            )
        )
        count = result.scalar() or 0
        num = count + 1
        now = datetime.now()
        # Thêm timestamp nhỏ để tránh trùng lặp nếu tạo quá nhanh
        suffix = str(int(time.time()))[-4:]
        return f"HD{now.year}{now.month:02d}{num:04d}{suffix}"

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

        # Get active contract (lấy bản mới nhất nếu lỡ có nhiều hơn 1)
        contract_result = await self.db.execute(
            select(Contract).where(
                Contract.room_id == room_id,
                Contract.organization_id == self.organization_id,
                Contract.status == "active",
            ).order_by(Contract.created_at.desc()).limit(1)
        )
        contract = contract_result.scalar_one_or_none()

        meter_result = await self.db.execute(
            select(MeterReading).where(
                MeterReading.room_id == room_id,
                MeterReading.organization_id == self.organization_id,
                MeterReading.reading_month == billing_month,
                MeterReading.reading_year == billing_year,
            ).order_by(MeterReading.recorded_at.desc()).limit(1)
        )
        meter = meter_result.scalar_one_or_none()

        rent_amount = contract.monthly_rent if contract else room.base_price
        electricity_amount = 0
        water_amount = 0

        if meter:
            electricity_amount = int((meter.electricity_usage or 0) * (room.electricity_price or 0))
            water_amount = int((meter.water_usage or 0) * (room.water_price or 0))

        parking_amount = (room.parking_fee or 0)
        v_count = (contract.vehicle_count if contract else 0) or 0
        if v_count > 0:
            parking_amount = (room.parking_fee or 0) * v_count

        # Lấy nợ cũ từ hóa đơn gần nhất
        old_debt = 0
        last_invoice_result = await self.db.execute(
            select(Invoice).where(
                Invoice.room_id == room_id,
                Invoice.organization_id == self.organization_id,
            ).order_by(Invoice.billing_year.desc(), Invoice.billing_month.desc()).limit(1)
        )
        last_invoice = last_invoice_result.scalar_one_or_none()
        if last_invoice:
            old_debt = max(0, last_invoice.total_amount - last_invoice.paid_amount)

        total = (
            (rent_amount or 0)
            + (electricity_amount or 0)
            + (water_amount or 0)
            + (room.internet_fee or 0)
            + parking_amount
            + old_debt
        )

        import calendar
        due_day = contract.payment_due_day if contract and contract.payment_due_day else 5
        _, last_day = calendar.monthrange(billing_year, billing_month)
        due_date = date(billing_year, billing_month, min(due_day, last_day))

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
            + data.old_debt
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
            vehicle_count=data.vehicle_count,
            other_amount=data.other_amount,
            discount_amount=data.discount_amount,
            old_debt=data.old_debt,
            total_amount=total,
            status="draft",
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
            "vietcombank": "970436",
            "bidv": "970418",
            "vietinbank": "970415",
            "techcombank": "970407",
            "mb bank": "970422",
            "mbbank": "970422",
            "tpbank": "970423",
            "acb": "970416",
            "vpbank": "970432",
            "agribank": "970405",
        }

        bank_name_norm = (org.bank_name or "").strip().lower()
        bank_bin = bank_map.get(bank_name_norm, "970436") # Default to VCB if not found but account exists
        
        amount = invoice.total_amount - invoice.paid_amount
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

    async def update_invoice(
        self,
        invoice_id: str,
        data: InvoiceCreate,
    ) -> InvoiceResponse:
        invoice_result = await self.db.execute(
            select(Invoice).where(
                Invoice.id == invoice_id,
                Invoice.organization_id == self.organization_id,
            )
        )
        invoice = invoice_result.scalar_one_or_none()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        if invoice.status != "draft":
            raise HTTPException(status_code=400, detail="Only draft invoices can be edited")

        # Update fields
        invoice.rent_amount = data.rent_amount
        invoice.electricity_amount = data.electricity_amount
        invoice.water_amount = data.water_amount
        invoice.internet_amount = data.internet_amount
        invoice.parking_amount = data.parking_amount
        invoice.vehicle_count = data.vehicle_count
        invoice.other_amount = data.other_amount
        invoice.old_debt = data.old_debt
        invoice.discount_amount = data.discount_amount
        invoice.due_date = data.due_date
        invoice.notes = data.notes
        
        invoice.total_amount = (
            data.rent_amount
            + data.electricity_amount
            + data.water_amount
            + data.internet_amount
            + data.parking_amount
            + data.other_amount
            + data.old_debt
            - data.discount_amount
        )
        
        # Regenerate QR because amount might change
        invoice.qr_code_url = await self._generate_banking_qr(invoice)
        
        await self.db.flush()
        await self.db.refresh(invoice)
        return InvoiceResponse.model_validate(invoice)

    async def confirm_invoice(self, invoice_id: str) -> InvoiceResponse:
        invoice_result = await self.db.execute(
            select(Invoice).where(
                Invoice.id == invoice_id,
                Invoice.organization_id == self.organization_id,
            )
        )
        invoice = invoice_result.scalar_one_or_none()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        if invoice.status != "draft":
            return InvoiceResponse.model_validate(invoice)
            
        invoice.status = "sent"
        await self.db.flush()
        await self.db.refresh(invoice)
        return InvoiceResponse.model_validate(invoice)
