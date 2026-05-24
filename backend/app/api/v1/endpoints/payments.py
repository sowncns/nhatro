from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
import time
import logging
from payos import PayOS
from payos.types import CreatePaymentLinkRequest
from datetime import datetime

from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.api.deps import require_owner
from app.core.config import settings
from app.database.models import Invoice, Payment, PaymentMethod, InvoiceStatus
from app.repositories.base import BaseRepository
from app.services.invoice_service import InvoiceService
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize PayOS
payos_client = None
if settings.PAYOS_CLIENT_ID and settings.PAYOS_API_KEY and settings.PAYOS_CHECKSUM_KEY:
    payos_client = PayOS(
        client_id=settings.PAYOS_CLIENT_ID,
        api_key=settings.PAYOS_API_KEY,
        checksum_key=settings.PAYOS_CHECKSUM_KEY
    )
else:
    logger.warning("PayOS credentials are not fully configured.")

@router.post("/{invoice_id}/create-link")
async def create_payment_link(
    invoice_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    if not payos_client:
        raise HTTPException(status_code=500, detail="PayOS is not configured")
    
    repo = BaseRepository(Invoice, db, ctx.organization_id)
    invoice = await repo.get(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(status_code=400, detail="Invoice is already paid")

    # Generate a unique integer order code
    order_code = int(time.time())
    
    # Store invoice number in description (PayOS limits description to 25 chars)
    description = f"PAY_{invoice.invoice_number}"
    
    # Calculate amount to pay (total - paid)
    amount_to_pay = invoice.total_amount - invoice.paid_amount
    if amount_to_pay <= 0:
        raise HTTPException(status_code=400, detail="Invoice is already fully paid")

    # PayOS requires amount to be at least 2000 VND
    if amount_to_pay < 2000:
        raise HTTPException(status_code=400, detail="Số tiền còn lại phải từ 2.000đ để thanh toán qua PayOS")
    
    payment_data = CreatePaymentLinkRequest(
        order_code=order_code,
        amount=amount_to_pay,
        description=description,
        cancel_url=settings.PAYOS_CANCEL_URL,
        return_url=settings.PAYOS_RETURN_URL
    )

    try:
        payment_link = payos_client.payment_requests.create(payment_data=payment_data)
        
        # Update invoice with checkout URL
        invoice.qr_code_url = payment_link.checkout_url
        await db.commit()
        
        return {"checkout_url": payment_link.checkout_url}
    except Exception as e:
        logger.error(f"Error creating PayOS payment link: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def webhook(request: Request, db: AsyncSession = Depends(get_db)):
    if not payos_client:
        raise HTTPException(status_code=500, detail="PayOS is not configured")
        
    body = await request.body()
    try:
        webhook_data = payos_client.webhooks.verify(body)
        logger.info(f"Received valid PayOS webhook: {webhook_data}")
        
        description = webhook_data.description
        if "PAY_" in description:
            invoice_number = description.split("PAY_")[1]
            
            # Find invoice by invoice_number
            from sqlalchemy import select
            result = await db.execute(select(Invoice).where(Invoice.invoice_number == invoice_number))
            invoice = result.scalar_one_or_none()
            
            if invoice and invoice.status != InvoiceStatus.PAID:
                # Record payment
                service = InvoiceService(db, invoice.organization_id)
                await service.record_payment(
                    invoice_id=invoice.id,
                    amount=webhook_data.amount,
                    payment_method="BANK_TRANSFER",
                    reference_number=str(webhook_data.order_code),
                    notes="Paid via PayOS"
                )
                logger.info(f"Invoice {invoice.id} marked as paid via PayOS")
                await db.commit()
                
        return {"success": True}
    except Exception as e:
        logger.error(f"Webhook verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature or data")


# ============ Landlord Payment Confirmation Endpoints ============

@router.get("/pending")
async def get_pending_payments(
    ctx: TenantContext = Depends(require_owner),
    db: AsyncSession = Depends(get_db)
):
    """Get all invoices waiting landlord verification based on PaymentProof."""
    try:
        from app.database.models import PaymentProof, ProofStatus, Invoice

        query = select(PaymentProof, Invoice).join(
            Invoice, PaymentProof.invoice_id == Invoice.id
        ).where(
            PaymentProof.organization_id == ctx.organization.id,
            PaymentProof.status == ProofStatus.PENDING
        )

        result = await db.execute(query)
        rows = result.all()

        items = []
        for proof, invoice in rows:
            items.append({
                "id": proof.id,
                "proof_id": proof.id,
                "invoice_id": invoice.id,
                "contract_id": invoice.contract_id,
                "amount": invoice.total_amount,
                "payment_method": "BANK_TRANSFER",
                "payment_date": proof.uploaded_at,
                "proof_image_url": proof.image_url,
                "notes": proof.note,
                "created_at": proof.uploaded_at
            })
        return items
    except Exception as e:
        logger.error(f"Error loading pending payments: {e}", exc_info=True)
        return []


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
