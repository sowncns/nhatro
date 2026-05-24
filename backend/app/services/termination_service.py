from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import calendar

from app.database.models import (
    Contract,
    ContractStatus,
    DebtRecord,
    DebtStatus,
    DepositAction,
    DepositTransaction,
    Invoice,
    InvoiceStatus,
    MeterReading,
    Organization,
    ReadingType,
    Room,
    RoomStatus,
    RoomTenant,
    TerminationHistory,
    TerminationType,
    User,
)
from app.schemas.schemas import InvoiceCreate
from app.services.invoice_service import InvoiceService


@dataclass(frozen=True)
class TerminationResult:
    contract_id: str
    contract_status: str
    termination_type: str
    termination_reason: str
    invoice_id: Optional[str]
    invoice_status: Optional[str]
    used_money: int
    utility_fee: int
    penalty_fee: int
    damage_fee: int
    deposit_used: int
    refund_amount: int
    remaining_debt: int
    need_manual_review: bool
    terminated_at: str
    terminated_by: str
    message: str


class TerminationService:
    def __init__(self, db: AsyncSession, organization_id: str, user_id: str):
        self.db = db
        self.organization_id = organization_id
        self.user_id = user_id
        self.invoice_service = InvoiceService(db, organization_id)

    @staticmethod
    def _apply_deposit(deposit_amount: int, total_due: int) -> tuple[int, int, int]:
        """
        Returns (deposit_used, refund_amount, remaining_debt)
        """
        deposit_amount = max(0, int(deposit_amount or 0))
        total_due = max(0, int(total_due or 0))
        deposit_used = min(deposit_amount, total_due)
        remaining_debt = max(0, total_due - deposit_used)
        refund_amount = max(0, deposit_amount - deposit_used)
        return deposit_used, refund_amount, remaining_debt

    async def execute(
        self,
        contract_id: str,
        termination_type: TerminationType,
        reason: str,
        note: str | None,
        actual_end_date: date,
        final_electricity: float | None = None,
        final_water: float | None = None,
        penalty_fee: int = 0,
        damage_fee: int = 0,
        cleaning_fee: int = 0,
        other_fee: int = 0,
        refund_unused_rent: int = 0,
        compensation_fee: int = 0,
        force: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> TerminationResult:
        contract = await self._get_contract(contract_id)
        if contract.status in (ContractStatus.CANCELLED, ContractStatus.TERMINATED, ContractStatus.ENDED):
            raise HTTPException(status_code=400, detail="Hợp đồng đã kết thúc hoặc bị hủy")

        if termination_type == TerminationType.ABANDONED_ROOM and not force:
            raise HTTPException(status_code=400, detail="ABANDONED_ROOM phải force terminate")

        # Enforce type-specific rules
        if termination_type == TerminationType.FORCE_MAJEURE:
            penalty_fee = 0
        if termination_type in (TerminationType.CONTRACT_EXPIRED, TerminationType.TENANT_EARLY_TERMINATION):
            # no refund unless explicitly provided by caller
            pass
        if termination_type == TerminationType.DEPOSIT_FORFEITURE:
            # Bỏ cọc chưa dọn vào: không cần chốt điện nước, mất cọc
            penalty_fee = 0
            damage_fee = 0
            cleaning_fee = 0
            other_fee = 0
            refund_unused_rent = 0
            compensation_fee = 0
            final_electricity = None
            final_water = None
        if termination_type == TerminationType.LANDLORD_TERMINATION and refund_unused_rent <= 0:
            refund_unused_rent = self.calc_unused_rent_refund(int(contract.monthly_rent or 0), actual_end_date)

        room = await self._get_room(contract.room_id)
        valid_user_id = await self._valid_user_id()

        async with self.db.begin_nested():
            old_status = contract.status

            if termination_type == TerminationType.DEPOSIT_FORFEITURE:
                elec_amount = 0
                water_amount = 0
                final_invoice = None
                total_due = 0
            else:
                elec_amount, water_amount = await self._create_final_meter_and_calc_utilities(
                    contract=contract,
                    room=room,
                    actual_end_date=actual_end_date,
                    final_electricity=final_electricity,
                    final_water=final_water,
                    recorded_by=valid_user_id,
                )

                final_invoice = await self._create_or_update_final_invoice(
                    contract=contract,
                    room=room,
                    actual_end_date=actual_end_date,
                    termination_type=termination_type,
                    elec_amount=elec_amount,
                    water_amount=water_amount,
                    penalty_fee=int(penalty_fee or 0),
                    damage_fee=int(damage_fee or 0),
                    cleaning_fee=int(cleaning_fee or 0),
                    other_fee=int(other_fee or 0),
                    refund_unused_rent=int(refund_unused_rent or 0),
                    compensation_fee=int(compensation_fee or 0),
                    note_prefix=termination_type.value,
                )

                total_due = max(0, int(final_invoice.total_amount or 0) - int(final_invoice.paid_amount or 0))
            deposit_used, refund_amount, remaining_debt = self._apply_deposit(
                deposit_amount=int(contract.deposit_amount or 0),
                total_due=total_due,
            )

            if termination_type == TerminationType.ABANDONED_ROOM:
                await self._auto_deduct_deposit(contract, deposit_used, valid_user_id)
                if refund_amount > 0:
                    # abandoned: never refund, keep as 0
                    refund_amount = 0
            elif termination_type == TerminationType.DEPOSIT_FORFEITURE:
                # Bỏ cọc chưa dọn vào: mất toàn bộ tiền cọc, không hoàn
                full_deposit = int(contract.deposit_amount or 0)
                await self._auto_deduct_deposit(contract, full_deposit, valid_user_id)
                deposit_used = full_deposit
                refund_amount = 0
            elif termination_type == TerminationType.LANDLORD_TERMINATION:
                # landlord termination: always refund remaining deposit
                await self._settle_deposit(contract, deposit_used, refund_amount, valid_user_id)
            elif termination_type == TerminationType.FORCE_MAJEURE:
                # force majeure: no penalty, refund remaining deposit
                await self._settle_deposit(contract, deposit_used, refund_amount, valid_user_id)
            else:
                await self._settle_deposit(contract, deposit_used, refund_amount, valid_user_id)

            need_manual_review = remaining_debt > 0 and termination_type == TerminationType.ABANDONED_ROOM
            if remaining_debt > 0:
                await self._create_debt_record(contract, final_invoice, remaining_debt, need_manual_review)

            await self._close_contract_and_room(contract, room, actual_end_date, termination_type, reason, note)

            history = await self._create_history(
                contract=contract,
                termination_type=termination_type,
                reason=reason,
                note=note,
                created_by=valid_user_id,
                final_invoice=final_invoice,
                deposit_used=deposit_used,
                refund_amount=refund_amount,
                remaining_debt=remaining_debt,
                metadata=metadata or {},
            )

        terminated_at = contract.terminated_at or datetime.now(timezone.utc)
        invoice_status = None
        used_money = 0
        if final_invoice:
            invoice_status = final_invoice.status.value if hasattr(final_invoice.status, "value") else str(final_invoice.status)
            used_money = int(final_invoice.total_amount or 0)

        return TerminationResult(
            contract_id=str(contract.id),
            contract_status=contract.status.value if hasattr(contract.status, "value") else str(contract.status),
            termination_type=termination_type.value,
            termination_reason=reason,
            invoice_id=str(final_invoice.id) if final_invoice else None,
            invoice_status=invoice_status,
            used_money=used_money,
            utility_fee=int(elec_amount + water_amount),
            penalty_fee=int(penalty_fee or 0),
            damage_fee=int(damage_fee or 0),
            deposit_used=int(deposit_used),
            refund_amount=int(refund_amount),
            remaining_debt=int(remaining_debt),
            need_manual_review=bool(need_manual_review),
            terminated_at=terminated_at.isoformat(),
            terminated_by=str(valid_user_id) if valid_user_id else str(self.user_id),
            message=f"Termination recorded ({termination_type.value})",
        )

    @staticmethod
    def calc_unused_rent_refund(monthly_rent: int, actual_end_date: date) -> int:
        """
        Refund unused rent from the next day after actual_end_date to end of month.
        """
        monthly_rent = max(0, int(monthly_rent or 0))
        days_in_month = calendar.monthrange(actual_end_date.year, actual_end_date.month)[1]
        if actual_end_date.day >= days_in_month:
            return 0
        unused_days = days_in_month - actual_end_date.day
        # prorate by day
        return int(round(monthly_rent * (unused_days / days_in_month)))

    async def _get_contract(self, contract_id: str) -> Contract:
        res = await self.db.execute(
            select(Contract).where(
                Contract.id == contract_id,
                Contract.organization_id == self.organization_id,
            )
        )
        contract = res.scalar_one_or_none()
        if not contract:
            raise HTTPException(status_code=404, detail="Không tìm thấy hợp đồng")
        if getattr(contract, "is_archived", False):
            raise HTTPException(status_code=400, detail="Hợp đồng đã lưu trữ")
        return contract

    async def _get_room(self, room_id: str) -> Room:
        res = await self.db.execute(select(Room).where(Room.id == room_id))
        room = res.scalar_one_or_none()
        if not room:
            raise HTTPException(status_code=404, detail="Không tìm thấy phòng")
        return room

    async def _valid_user_id(self) -> Optional[str]:
        res = await self.db.execute(select(User.id).where(User.id == self.user_id))
        return self.user_id if res.scalar() else None

    async def _create_final_meter_and_calc_utilities(
        self,
        contract: Contract,
        room: Room,
        actual_end_date: date,
        final_electricity: float | None,
        final_water: float | None,
        recorded_by: Optional[str],
    ) -> int:
        # If no final meter provided, treat as 0 utility for termination workflow (used for FORCE_MAJEURE etc.)
        if final_electricity is None or final_water is None:
            return 0

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
            period_start=date.today(),
            period_end=actual_end_date,
            reading_month=actual_end_date.month,
            reading_year=actual_end_date.year,
            electricity_previous=elec_prev,
            electricity_current=final_electricity,
            electricity_usage=max(0, final_electricity - elec_prev),
            water_previous=water_prev,
            water_current=final_water,
            water_usage=max(0, final_water - water_prev),
            is_locked=True,
            notes=f"Chốt số cuối kỳ - HĐ {contract.contract_number}",
            recorded_by=recorded_by,
        )
        self.db.add(final_meter)
        await self.db.flush()

        elec_amount = int(final_meter.electricity_usage * (room.electricity_price or 0))
        water_amount = int(final_meter.water_usage * (room.water_price or 0))
        return elec_amount, water_amount

    async def _create_or_update_final_invoice(
        self,
        contract: Contract,
        room: Room,
        actual_end_date: date,
        termination_type: TerminationType,
        elec_amount: int,
        water_amount: int,
        penalty_fee: int,
        damage_fee: int,
        cleaning_fee: int,
        other_fee: int,
        refund_unused_rent: int,
        compensation_fee: int,
        note_prefix: str,
    ) -> Invoice:
        # Find existing invoice for the period
        billing_month = actual_end_date.month
        billing_year = actual_end_date.year
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

        # Handle org settings fallbacks
        org_result = await self.db.execute(select(Organization).where(Organization.id == self.organization_id))
        org = org_result.scalar_one_or_none()
        org_settings = org.settings if org and org.settings else {}

        default_internet = org_settings.get('default_internet_fee', 0) or 0
        internet_amount = int(room.internet_fee or default_internet)
        
        default_parking = org_settings.get('default_parking_fee', 0) or 0
        parking_per_vehicle = room.parking_fee or default_parking
        v_count = int(contract.vehicle_count or 0)
        parking_amount = parking_per_vehicle * v_count if v_count > 0 else parking_per_vehicle
        
        default_service = org_settings.get('default_service_fee', 0) or 0
            
        rent_amount = int(contract.monthly_rent or 0)
        discount_amount = max(0, int(refund_unused_rent or 0))
        
        other_amount = int(other_fee or 0) + int(penalty_fee or 0) + int(damage_fee or 0) + int(cleaning_fee or 0) + int(compensation_fee or 0)

        if termination_type == TerminationType.ABANDONED_ROOM:
            import calendar
            days_in_month = calendar.monthrange(billing_year, billing_month)[1]
            days_used = actual_end_date.day
            total_fixed_fees = rent_amount + internet_amount + parking_amount + int(default_service)
            prorated_rent = int(round(total_fixed_fees * (days_used / days_in_month)))
            
            rent_amount = prorated_rent
            internet_amount = 0
            parking_amount = 0
            other_amount = 0
            discount_amount = 0

        invoice_data = InvoiceCreate(
            room_id=str(room.id),
            billing_month=billing_month,
            billing_year=billing_year,
            rent_amount=rent_amount,
            electricity_amount=elec_amount,
            water_amount=water_amount,
            internet_amount=internet_amount,
            parking_amount=parking_amount,
            vehicle_count=v_count,
            other_amount=other_amount,
            discount_amount=discount_amount,
            old_debt=0,
            due_date=actual_end_date,
            notes=f"FINAL[{note_prefix}] Hóa đơn chốt - HĐ {contract.contract_number}",
        )

        if current_invoice:
            current_invoice.contract_id = current_invoice.contract_id or contract.id
            current_invoice.rent_amount = invoice_data.rent_amount
            current_invoice.electricity_amount = invoice_data.electricity_amount
            current_invoice.water_amount = invoice_data.water_amount
            current_invoice.internet_amount = invoice_data.internet_amount
            current_invoice.parking_amount = invoice_data.parking_amount
            current_invoice.vehicle_count = invoice_data.vehicle_count
            current_invoice.other_amount = invoice_data.other_amount
            current_invoice.discount_amount = invoice_data.discount_amount
            
            # Recalculate total
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
            current_invoice.due_date = invoice_data.due_date
            current_invoice.notes = invoice_data.notes
            current_invoice.qr_code_url = await self.invoice_service._generate_banking_qr(current_invoice)
            remaining = int(current_invoice.total_amount or 0) - int(current_invoice.paid_amount or 0)
            if remaining <= 0:
                current_invoice.status = InvoiceStatus.PAID
                current_invoice.paid_at = datetime.now(timezone.utc)
            else:
                current_invoice.status = InvoiceStatus.UNPAID
            # Archive immediately: hóa đơn chốt đưa vào lưu trữ
            current_invoice.archived_at = datetime.now(timezone.utc)
            await self.db.flush()
            return current_invoice

        created = await self.invoice_service.create_invoice(invoice_data, contract_id=str(contract.id))
        # InvoiceService returns InvoiceResponse; reload Invoice ORM
        inv_obj = await self.db.get(Invoice, created.id)
        if not inv_obj:
            raise HTTPException(status_code=500, detail="Không thể tạo hóa đơn chốt")
        inv_obj.status = InvoiceStatus.UNPAID
        # Archive immediately: hóa đơn chốt đưa vào lưu trữ
        inv_obj.archived_at = datetime.now(timezone.utc)
        await self.db.flush()
        return inv_obj

    async def _auto_deduct_deposit(self, contract: Contract, deposit_used: int, performed_by: Optional[str]):
        if deposit_used <= 0:
            return
        self.db.add(
            DepositTransaction(
                organization_id=self.organization_id,
                contract_id=contract.id,
                amount=int(deposit_used),
                type=DepositAction.DEDUCTION,
                reason="Tự động cấn trừ tiền cọc cho hóa đơn chốt (ABANDONED_ROOM)",
                performed_by=performed_by,
            )
        )
        contract.deposit_returned = True

    async def _settle_deposit(self, contract: Contract, deposit_used: int, refund_amount: int, performed_by: Optional[str]):
        if deposit_used > 0:
            self.db.add(
                DepositTransaction(
                    organization_id=self.organization_id,
                    contract_id=contract.id,
                    amount=int(deposit_used),
                    type=DepositAction.DEDUCTION,
                    reason="Cấn trừ tiền cọc khi thanh lý",
                    performed_by=performed_by,
                )
            )
        if refund_amount > 0:
            self.db.add(
                DepositTransaction(
                    organization_id=self.organization_id,
                    contract_id=contract.id,
                    amount=int(refund_amount),
                    type=DepositAction.REFUND,
                    reason="Hoàn tiền cọc khi kết thúc hợp đồng",
                    performed_by=performed_by,
                )
            )
        contract.deposit_returned = True

    async def _create_debt_record(self, contract: Contract, invoice: Invoice, remaining_debt: int, risk_flag: bool):
        if remaining_debt <= 0:
            return
        rec = DebtRecord(
            organization_id=self.organization_id,
            contract_id=contract.id,
            tenant_id=contract.tenant_id,
            invoice_id=invoice.id,
            amount=int(remaining_debt),
            status=DebtStatus.OPEN,
            risk_flag=bool(risk_flag),
            note="Debt created from termination workflow",
        )
        self.db.add(rec)

    async def _close_contract_and_room(
        self,
        contract: Contract,
        room: Room,
        actual_end_date: date,
        termination_type: TerminationType,
        reason: str,
        note: str | None,
    ):
        # mark tenants moved out
        await self.db.execute(
            update(RoomTenant)
            .where(RoomTenant.room_id == room.id, RoomTenant.is_active == True)
            .values(is_active=False, move_out_date=actual_end_date, move_out_reason=reason)
        )
        room.status = RoomStatus.AVAILABLE

        if termination_type == TerminationType.ABANDONED_ROOM:
            contract.status = ContractStatus.ABANDONED_ROOM
        else:
            contract.status = ContractStatus.TERMINATED
        contract.actual_end_date = actual_end_date
        contract.termination_note = note
        contract.terminated_at = datetime.now(timezone.utc)

    async def _create_history(
        self,
        contract: Contract,
        termination_type: TerminationType,
        reason: str,
        note: str | None,
        created_by: Optional[str],
        final_invoice: Optional[Invoice],
        deposit_used: int,
        refund_amount: int,
        remaining_debt: int,
        metadata: dict[str, Any],
    ) -> TerminationHistory:
        snapshot = {
            "id": str(contract.id),
            "contract_number": contract.contract_number,
            "room_id": str(contract.room_id),
            "tenant_id": str(contract.tenant_id),
            "start_date": contract.start_date.isoformat() if contract.start_date else None,
            "end_date": contract.end_date.isoformat() if contract.end_date else None,
            "actual_end_date": contract.actual_end_date.isoformat() if contract.actual_end_date else None,
            "monthly_rent": int(contract.monthly_rent or 0),
            "deposit_amount": int(contract.deposit_amount or 0),
            "status": contract.status.value if hasattr(contract.status, "value") else str(contract.status),
        }
        hist = TerminationHistory(
            organization_id=self.organization_id,
            contract_id=contract.id,
            termination_type=termination_type,
            reason=reason,
            note=note,
            created_by=created_by,
            final_invoice_id=final_invoice.id if final_invoice else None,
            deposit_used=int(deposit_used),
            refund_amount=int(refund_amount),
            remaining_debt=int(remaining_debt),
            contract_snapshot=snapshot,
            metadata_=metadata,
        )
        self.db.add(hist)
        await self.db.flush()
        return hist
