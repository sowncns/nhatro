"""Payment endpoints for landlords"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.api.deps import require_owner, TenantContext
from app.database.models import Payment, Invoice, InvoiceStatus
from datetime import datetime

router = APIRouter()


@router.get("/pending")
async def get_pending_payments(
    ctx: TenantContext = Depends(require_owner),
    db: AsyncSession = Depends(get_db)
):
    """Get all pending payment confirmations"""
    query = select(Payment).where(
        Payment.organization_id == ctx.organization.id,
        Payment.status == "pending"
    ).order_by(Payment.created_at.desc())

    result = await db.execute(query)
    payments = result.scalars().all()

    return [
        {
            "id": p.id,
            "invoice_id": p.invoice_id,
            "contract_id": p.contract_id,
            "amount": p.amount,
            "payment_method": p.payment_method,
            "payment_date": p.payment_date,
            "proof_image_url": p.proof_image_url,
            "notes": p.notes,
            "created_at": p.created_at
        }
        for p in payments
    ]


@router.post("/{payment_id}/confirm")
async def confirm_payment(
    payment_id: str,
    ctx: TenantContext = Depends(require_owner),
    db: AsyncSession = Depends(get_db)
):
    """Confirm payment and mark invoice as paid"""
    # Get payment
    query = select(Payment).where(
        Payment.id == payment_id,
        Payment.organization_id == ctx.organization.id
    )
    result = await db.execute(query)
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Không tìm thấy thanh toán")

    if payment.status != "pending":
        raise HTTPException(status_code=400, detail="Thanh toán đã được xử lý")

    # Update payment status
    payment.status = "confirmed"
    payment.confirmed_by = ctx.user.id
    payment.confirmed_at = datetime.now()

    # Update invoice status
    if payment.invoice_id:
        invoice_query = select(Invoice).where(Invoice.id == payment.invoice_id)
        invoice_result = await db.execute(invoice_query)
        invoice = invoice_result.scalar_one_or_none()

        if invoice:
            remaining = (invoice.total_amount or 0) - (invoice.paid_amount or 0)
            if remaining <= 0:
                raise HTTPException(status_code=400, detail="Hóa đơn đã được thanh toán đủ")
            if payment.amount != remaining:
                raise HTTPException(
                    status_code=400,
                    detail=f"Vui lòng xác nhận thanh toán đủ số tiền còn lại: {remaining}",
                )

            invoice.paid_amount = (invoice.paid_amount or 0) + payment.amount
            invoice.status = InvoiceStatus.PAID
            invoice.paid_at = datetime.now()

    await db.commit()

    return {
        "message": "Xác nhận thanh toán thành công",
        "payment_id": payment.id,
        "invoice_id": payment.invoice_id
    }


@router.post("/{payment_id}/reject")
async def reject_payment(
    payment_id: str,
    reason: str,
    ctx: TenantContext = Depends(require_owner),
    db: AsyncSession = Depends(get_db)
):
    """Reject payment proof"""
    # Get payment
    query = select(Payment).where(
        Payment.id == payment_id,
        Payment.organization_id == ctx.organization.id
    )
    result = await db.execute(query)
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Không tìm thấy thanh toán")

    if payment.status != "pending":
        raise HTTPException(status_code=400, detail="Thanh toán đã được xử lý")

    # Update payment status
    payment.status = "rejected"
    payment.notes = f"{payment.notes}\n\nLý do từ chối: {reason}"

    # Update invoice back to unpaid
    if payment.invoice_id:
        invoice_query = select(Invoice).where(Invoice.id == payment.invoice_id)
        invoice_result = await db.execute(invoice_query)
        invoice = invoice_result.scalar_one_or_none()

        if invoice:
            invoice.status = InvoiceStatus.SENT

    await db.commit()

    return {
        "message": "Đã từ chối thanh toán",
        "payment_id": payment.id,
        "reason": reason
    }
