from datetime import date, datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException

from app.database.models import (
    Contract, Room, Tenant, RoomTenant, MeterReading, 
    Invoice, DepositTransaction, ContractLog, User,
    ContractStatus, RoomStatus, DepositAction, ReadingType, InvoiceStatus
)
from app.schemas.schemas import ContractTerminateRequest, InvoiceCreate
from app.services.invoice_service import InvoiceService


class ContractTerminationService:
    def __init__(self, db: AsyncSession, organization_id: str, user_id: str):
        self.db = db
        self.organization_id = organization_id
        self.user_id = user_id
        self.invoice_service = InvoiceService(db, organization_id)

    async def terminate_contract(self, contract_id: str, data: ContractTerminateRequest):
        """
        Full business flow for terminating a contract.
        """
        try:
            # 1. Fetch Contract and related Room
            contract_result = await self.db.execute(
                select(Contract).where(
                    Contract.id == contract_id,
                    Contract.organization_id == self.organization_id
                )
            )
            contract = contract_result.scalar_one_or_none()
            if not contract:
                raise HTTPException(status_code=404, detail="Không tìm thấy hợp đồng")
            
            if contract.status in [ContractStatus.ENDED, ContractStatus.CANCELLED, ContractStatus.TERMINATED]:
                raise HTTPException(status_code=400, detail="Hợp đồng này đã được kết thúc hoặc hủy trước đó")

            room_result = await self.db.execute(
                select(Room).where(Room.id == contract.room_id)
            )
            room = room_result.scalar_one_or_none()
            if not room:
                raise HTTPException(status_code=404, detail="Không tìm thấy phòng")

            # Check if user exists for recorded_by FK
            user_check = await self.db.execute(select(User.id).where(User.id == self.user_id))
            valid_user_id = self.user_id if user_check.scalar() else None

            # Start atomic transaction
            async with self.db.begin_nested():
                old_status = contract.status
                
                # 2. Record Final Meter Reading
                prev_meter_result = await self.db.execute(
                    select(MeterReading)
                    .where(MeterReading.room_id == room.id)
                    .order_by(MeterReading.recorded_at.desc())
                    .limit(1)
                )
                prev_meter = prev_meter_result.scalar_one_or_none()
                
                elec_prev = (prev_meter.electricity_current or 0) if prev_meter else 0
                water_prev = (prev_meter.water_current or 0) if prev_meter else 0
                
                final_meter = MeterReading(
                    organization_id=self.organization_id,
                    room_id=room.id,
                    contract_id=contract.id,
                    reading_type=ReadingType.FINAL,
                    period_start=date.today(), # Tạm thời lấy ngày hiện tại
                    period_end=data.actual_end_date,
                    reading_month=data.actual_end_date.month,
                    reading_year=data.actual_end_date.year,
                    electricity_previous=elec_prev,
                    electricity_current=data.final_electricity,
                    electricity_usage=max(0, data.final_electricity - elec_prev),
                    water_previous=water_prev,
                    water_current=data.final_water,
                    water_usage=max(0, data.final_water - water_prev),
                    is_locked=True,
                    notes=f"Chốt số cuối kỳ - HĐ {contract.contract_number}",
                    recorded_by=valid_user_id
                )
                self.db.add(final_meter)
                await self.db.flush()

                # 3. Generate or update final invoice for the move-out period.
                elec_amount = int(final_meter.electricity_usage * (room.electricity_price or 0))
                water_amount = int(final_meter.water_usage * (room.water_price or 0))

                billing_month = data.actual_end_date.month
                billing_year = data.actual_end_date.year

                current_invoice_result = await self.db.execute(
                    select(Invoice)
                    .where(
                        Invoice.room_id == room.id,
                        Invoice.organization_id == self.organization_id,
                        Invoice.billing_month == billing_month,
                        Invoice.billing_year == billing_year,
                        Invoice.status != InvoiceStatus.CANCELLED,
                    )
                    .order_by(Invoice.created_at.desc())
                    .limit(1)
                )
                current_invoice = current_invoice_result.scalar_one_or_none()

                last_invoice_result = await self.db.execute(
                    select(Invoice)
                    .where(
                        Invoice.room_id == room.id,
                        Invoice.organization_id == self.organization_id,
                        Invoice.status != InvoiceStatus.CANCELLED,
                        ~(
                            (Invoice.billing_month == billing_month)
                            & (Invoice.billing_year == billing_year)
                        ),
                    )
                    .order_by(Invoice.billing_year.desc(), Invoice.billing_month.desc(), Invoice.created_at.desc())
                    .limit(1)
                )
                last_invoice = last_invoice_result.scalar_one_or_none()
                old_debt = (
                    current_invoice.old_debt
                    if current_invoice and current_invoice.old_debt is not None
                    else max(0, (last_invoice.total_amount or 0) - (last_invoice.paid_amount or 0)) if last_invoice else 0
                )

                # Get org defaults for fees
                from app.database.models import Organization
                org_result = await self.db.execute(
                    select(Organization).where(Organization.id == self.organization_id)
                )
                org = org_result.scalar_one_or_none()
                org_settings = (org.settings or {}) if org else {}
                
                default_parking = org_settings.get('default_parking_fee', 0) or 0
                default_internet = org_settings.get('default_internet_fee', 0) or 0
                
                parking_fee = room.parking_fee or default_parking
                internet_fee = room.internet_fee or default_internet

                invoice_data = InvoiceCreate(
                    room_id=room.id,
                    billing_month=billing_month,
                    billing_year=billing_year,
                    rent_amount=contract.monthly_rent,
                    electricity_amount=elec_amount,
                    water_amount=water_amount,
                    internet_amount=internet_fee,
                    parking_amount=parking_fee * (contract.vehicle_count or 0),
                    vehicle_count=contract.vehicle_count or 0,
                    old_debt=old_debt,
                    due_date=data.actual_end_date,
                    notes=f"Hóa đơn thanh lý hợp đồng {contract.contract_number}"
                )
                if current_invoice:
                    current_invoice.contract_id = current_invoice.contract_id or contract.id
                    current_invoice.rent_amount = invoice_data.rent_amount
                    current_invoice.electricity_amount = invoice_data.electricity_amount
                    current_invoice.water_amount = invoice_data.water_amount
                    current_invoice.internet_amount = invoice_data.internet_amount
                    current_invoice.parking_amount = invoice_data.parking_amount
                    current_invoice.vehicle_count = invoice_data.vehicle_count
                    current_invoice.old_debt = invoice_data.old_debt
                    current_invoice.due_date = invoice_data.due_date
                    current_invoice.notes = invoice_data.notes
                    current_invoice.total_amount = (
                        (current_invoice.rent_amount or 0)
                        + (current_invoice.electricity_amount or 0)
                        + (current_invoice.water_amount or 0)
                        + (current_invoice.internet_amount or 0)
                        + (current_invoice.parking_amount or 0)
                        + (current_invoice.other_amount or 0)
                        + (current_invoice.old_debt or 0)
                        - (current_invoice.discount_amount or 0)
                    )
                    current_invoice.qr_code_url = await self.invoice_service._generate_banking_qr(current_invoice)
                    if (current_invoice.paid_amount or 0) >= current_invoice.total_amount:
                        current_invoice.status = InvoiceStatus.PAID
                    elif (current_invoice.paid_amount or 0) > 0:
                        current_invoice.status = InvoiceStatus.SENT
                    await self.db.flush()
                else:
                    await self.invoice_service.create_invoice(invoice_data, contract_id=contract.id)

                # 4. Settle Deposit
                for deduction in data.deposit_deductions:
                    settlement = DepositTransaction(
                        organization_id=self.organization_id,
                        contract_id=contract.id,
                        amount=deduction.amount,
                        type=DepositAction.DEDUCTION,
                        reason=deduction.reason,
                        performed_by=valid_user_id
                    )
                    self.db.add(settlement)
                
                if data.refund_amount > 0:
                    refund = DepositTransaction(
                        organization_id=self.organization_id,
                        contract_id=contract.id,
                        amount=data.refund_amount,
                        type=DepositAction.REFUND,
                        reason="Hoàn trả tiền cọc khi kết thúc hợp đồng",
                        performed_by=valid_user_id
                    )
                    self.db.add(refund)
                
                contract.deposit_returned = True

                # 5. Update Tenant and Room statuses
                await self.db.execute(
                    update(RoomTenant)
                    .where(RoomTenant.room_id == room.id, RoomTenant.is_active == True)
                    .values(
                        is_active=False, 
                        move_out_date=data.actual_end_date,
                        move_out_reason=data.move_out_reason
                    )
                )

                room.status = RoomStatus.AVAILABLE
                contract.status = ContractStatus.TERMINATED
                contract.actual_end_date = data.actual_end_date
                contract.termination_note = data.termination_note
                contract.terminated_at = datetime.now(timezone.utc)

                # 6. Audit Logging
                log = ContractLog(
                    organization_id=self.organization_id,
                    contract_id=contract.id,
                    action="TERMINATE",
                    old_status=old_status,
                    new_status=ContractStatus.TERMINATED,
                    new_data={
                        "actual_end_date": str(data.actual_end_date),
                        "refund_amount": data.refund_amount,
                        "deductions": [d.model_dump() for d in data.deposit_deductions]
                    },
                    performed_by=valid_user_id
                )
                self.db.add(log)
                await self.db.flush()
            
            return contract
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error in terminate_contract: {e}")
            raise HTTPException(status_code=500, detail=f"Lỗi xử lý thanh lý: {str(e)}")
        
        return contract

    async def cancel_contract(self, contract_id: str, reason: str):
        """
        Cancel a contract that hasn't started or is being voided.
        """
        contract_result = await self.db.execute(
            select(Contract).where(
                Contract.id == contract_id,
                Contract.organization_id == self.organization_id
            )
        )
        contract = contract_result.scalar_one_or_none()
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")

        async with self.db.begin_nested():
            old_status = contract.status
            contract.status = ContractStatus.CANCELLED
            contract.cancel_reason = reason
            contract.terminated_at = datetime.now(timezone.utc)

            # Update Room status
            room_result = await self.db.execute(
                select(Room).where(Room.id == contract.room_id)
            )
            room = room_result.scalar_one_or_none()
            if room:
                room.status = RoomStatus.AVAILABLE

            # Audit Log
            log = ContractLog(
                organization_id=self.organization_id,
                contract_id=contract.id,
                action="CANCEL",
                old_status=old_status,
                new_status=ContractStatus.CANCELLED,
                new_data={"reason": reason},
                performed_by=self.user_id
            )
            self.db.add(log)
            await self.db.flush()
        
        return contract
