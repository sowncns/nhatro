"""Invoices Endpoints"""
import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.models.models import Invoice
from app.schemas.schemas import InvoiceCreate, InvoiceResponse, PaginatedResponse, InvoiceBulkEmailRequest
from app.repositories.base import BaseRepository
from app.services.invoice_service import InvoiceService
from app.services.cache_service import CacheService
from app.services.invalidate_helper import InvalidateHelper
from app.core.cache_constants import TTL_INVOICE_LIST, TTL_INVOICE_DETAIL
from app.core.config import settings

router = APIRouter()


def _format_vnd(amount: int) -> str:
    return f"{amount:,.0f}".replace(",", ".") + " đ"


async def _send_invoice_email(email: str, subject: str, html: str):
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        raise ValueError("SMTP_USER and SMTP_PASSWORD are required to send invoice email")

    sender = settings.EMAIL_FROM or settings.SMTP_USER
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = email
    message.attach(MIMEText(html, "html", "utf-8"))

    def send_mail():
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, [email], message.as_string())

    await asyncio.to_thread(send_mail)


def _invoice_email_html(invoice, tenant, room, organization) -> str:
    remaining = (invoice.total_amount or 0) - (invoice.paid_amount or 0)
    qr_html = ""
    if invoice.qr_code_url:
        qr_html = f"""
        <p style="margin: 16px 0 8px; font-weight: 600;">Quét mã để thanh toán</p>
        <img src="{invoice.qr_code_url}" alt="QR thanh toán" style="width: 180px; height: 180px; border: 1px solid #e2e8f0; border-radius: 12px;" />
        """

    return f"""
    <div style="font-family: Arial, sans-serif; color: #0f172a; line-height: 1.55; max-width: 640px;">
      <h2 style="margin: 0 0 8px;">Hóa đơn {invoice.invoice_number}</h2>
      <p style="margin: 0 0 16px;">Xin chào {tenant.full_name},</p>
      <p>{organization.name} gửi hóa đơn phòng <strong>{room.room_number}</strong> kỳ <strong>{invoice.billing_month}/{invoice.billing_year}</strong>.</p>
      <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
        <tr><td style="padding: 8px; border: 1px solid #e2e8f0;">Tiền phòng</td><td style="padding: 8px; border: 1px solid #e2e8f0; text-align: right;">{_format_vnd(invoice.rent_amount or 0)}</td></tr>
        <tr><td style="padding: 8px; border: 1px solid #e2e8f0;">Điện</td><td style="padding: 8px; border: 1px solid #e2e8f0; text-align: right;">{_format_vnd(invoice.electricity_amount or 0)}</td></tr>
        <tr><td style="padding: 8px; border: 1px solid #e2e8f0;">Nước</td><td style="padding: 8px; border: 1px solid #e2e8f0; text-align: right;">{_format_vnd(invoice.water_amount or 0)}</td></tr>
        <tr><td style="padding: 8px; border: 1px solid #e2e8f0;">Internet</td><td style="padding: 8px; border: 1px solid #e2e8f0; text-align: right;">{_format_vnd(invoice.internet_amount or 0)}</td></tr>
        <tr><td style="padding: 8px; border: 1px solid #e2e8f0;">Gửi xe</td><td style="padding: 8px; border: 1px solid #e2e8f0; text-align: right;">{_format_vnd(invoice.parking_amount or 0)}</td></tr>
        <tr><td style="padding: 8px; border: 1px solid #e2e8f0;">Nợ cũ</td><td style="padding: 8px; border: 1px solid #e2e8f0; text-align: right;">{_format_vnd(invoice.old_debt or 0)}</td></tr>
        <tr><td style="padding: 10px; border: 1px solid #e2e8f0; font-weight: 700;">Cần thanh toán</td><td style="padding: 10px; border: 1px solid #e2e8f0; text-align: right; color: #dc2626; font-weight: 700;">{_format_vnd(remaining)}</td></tr>
      </table>
      <p> <strong>VUI LÒNG GIỮ LẠI HÓA ĐƠN THANH TOÁN ĐỂ GỬI MINH CHỨNG CHO CHỦ TRỌ TRÊN TRONG DÀNH CHO NGƯỜI THUÊ TRỌ</strong></p>
      <p>Hạn thanh toán: <strong>{invoice.due_date.strftime("%d/%m/%Y")}</strong></p>
      {qr_html}
      <p style="margin-top: 18px; color: #64748b; font-size: 13px;">Nếu đã thanh toán, vui lòng bỏ qua email này hoặc gửi minh chứng trong cổng khách thuê.</p>
    </div>
    """


@router.get("", response_model=PaginatedResponse)
async def list_invoices(
    page: int = Query(1, ge=1),
    size: int = Query(20),
    status: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    room_id: Optional[str] = None,
    mode: str = Query("active"),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"invoices:list:{ctx.organization_id}:{page}:{size}:{status}:{month}:{year}:{room_id}:{mode}"
    cached = await CacheService.get(cache_key)
    if cached:
        return cached

    repo = BaseRepository(Invoice, db, ctx.organization_id)
    filters = []
    if status:
        filters.append(Invoice.status == status)
    if month:
        filters.append(Invoice.billing_month == month)
    if year:
        filters.append(Invoice.billing_year == year)
    if room_id:
        filters.append(Invoice.room_id == room_id)
    total = await repo.count(filters, mode=mode)
    items = await repo.get_all(skip=(page - 1) * size, limit=size, filters=filters,
                                order_by=Invoice.created_at.desc(), mode=mode)

    # Fetch tenant names from contracts
    contract_ids = [inv.contract_id for inv in items if inv.contract_id]
    tenant_names_map = {}
    if contract_ids:
        from app.database.models import Contract, Tenant
        contract_result = await db.execute(
            select(Contract).where(Contract.id.in_(contract_ids))
        )
        contracts = contract_result.scalars().all()

        # Get tenant IDs from contracts
        tenant_ids = [c.tenant_id for c in contracts if c.tenant_id]
        if tenant_ids:
            tenant_result = await db.execute(
                select(Tenant).where(Tenant.id.in_(tenant_ids))
            )
            tenants = {t.id: t.full_name for t in tenant_result.scalars().all()}

            # Map contract_id to tenant name
            for c in contracts:
                if c.tenant_id:
                    tenant_names_map[c.id] = tenants.get(c.tenant_id, "N/A")

    formatted_items = []
    for inv in items:
        resp = InvoiceResponse.model_validate(inv)
        if hasattr(resp, 'representative_name'):
            resp.representative_name = tenant_names_map.get(inv.contract_id, "N/A")
        formatted_items.append(resp)
        
    res = PaginatedResponse(
        items=formatted_items,
        total=total, page=page, size=size,
        pages=(total + size - 1) // size,
    )
    await CacheService.set(cache_key, res.model_dump(), expire=TTL_INVOICE_LIST)
    return res


@router.post("", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    data: InvoiceCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    from app.models.models import Contract, ContractStatus
    
    service = InvoiceService(db, ctx.organization_id)
    
    # Automatically find active contract for this room
    contract_result = await db.execute(
        select(Contract).where(
            Contract.room_id == data.room_id,
            Contract.organization_id == ctx.organization_id,
            Contract.status == ContractStatus.ACTIVE,
        ).order_by(Contract.created_at.desc()).limit(1)
    )
    contract = contract_result.scalar_one_or_none()
    contract_id = contract.id if contract else None
    
    inv = await service.create_invoice(data, contract_id=contract_id)
    await InvalidateHelper.invalidate_invoice(ctx.organization_id)
    return inv


@router.post("/auto-generate")
async def auto_generate_invoices(
    billing_month: int,
    billing_year: int,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Auto-generate invoices for all occupied rooms"""
    from app.models.models import Room, RoomStatus
    rooms = await db.execute(
        select(Room).where(
            Room.organization_id == ctx.organization_id,
            Room.status == RoomStatus.OCCUPIED,
        )
    )
    service = InvoiceService(db, ctx.organization_id)
    generated = []
    errors = []
    for room in rooms.scalars():
        try:
            inv = await service.auto_generate_for_room(room.id, billing_month, billing_year)
            generated.append(inv.invoice_number)
        except Exception as e:
            errors.append({"room": room.room_number, "error": str(e)})
            
    await InvalidateHelper.invalidate_invoice(ctx.organization_id)
    return {"generated": generated, "errors": errors}


@router.post("/send-bulk-email")
async def send_bulk_invoice_email(
    data: InvoiceBulkEmailRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    from app.database.models import Contract, Tenant, Room, Organization, InvoiceStatus

    query = (
        select(Invoice, Contract, Tenant, Room, Organization)
        .join(Contract, Invoice.contract_id == Contract.id)
        .join(Tenant, Contract.tenant_id == Tenant.id)
        .join(Room, Invoice.room_id == Room.id)
        .join(Organization, Invoice.organization_id == Organization.id)
        .where(Invoice.organization_id == ctx.organization_id)
        .where(Invoice.status.notin_(
            [InvoiceStatus.DRAFT, 
            InvoiceStatus.CANCELLED,
            InvoiceStatus.PAID,
            InvoiceStatus.PENDING_CONFIRMATION,
            InvoiceStatus.REJECTED,
            ]))
    )

    if data.invoice_ids:
        query = query.where(Invoice.id.in_(data.invoice_ids))
    else:
        if not data.billing_month or not data.billing_year:
            raise HTTPException(status_code=400, detail="Vui lòng chọn tháng/năm hoặc danh sách hóa đơn")
        query = query.where(
            Invoice.billing_month == data.billing_month,
            Invoice.billing_year == data.billing_year,
        )

    result = await db.execute(query)
    rows = result.all()
    if not rows:
        return {
            "sent": 0,
            "skipped": 0,
            "failed": 0,
            "details": [],
            "message": "Không có hóa đơn đã chốt phù hợp để gửi",
        }

    details = []
    for invoice, contract, tenant, room, organization in rows:
        if not tenant.email:
            details.append({
                "invoice_number": invoice.invoice_number,
                "room_number": room.room_number,
                "tenant_name": tenant.full_name,
                "status": "skipped",
                "reason": "Người đại diện chưa có email",
            })
            continue

        try:
            await _send_invoice_email(
                tenant.email,
                f"Hóa đơn {invoice.invoice_number} - Phòng {room.room_number}",
                _invoice_email_html(invoice, tenant, room, organization),
            )
            details.append({
                "invoice_number": invoice.invoice_number,
                "room_number": room.room_number,
                "tenant_name": tenant.full_name,
                "email": tenant.email,
                "status": "sent",
            })
        except Exception as exc:
            details.append({
                "invoice_number": invoice.invoice_number,
                "room_number": room.room_number,
                "tenant_name": tenant.full_name,
                "email": tenant.email,
                "status": "failed",
                "reason": str(exc),
            })

    sent = sum(1 for item in details if item["status"] == "sent")
    skipped = sum(1 for item in details if item["status"] == "skipped")
    failed = sum(1 for item in details if item["status"] == "failed")
    return {"sent": sent, "skipped": skipped, "failed": failed, "details": details}


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"invoices:detail:{ctx.organization_id}:{invoice_id}"
    cached = await CacheService.get(cache_key)
    if cached:
        return cached

    repo = BaseRepository(Invoice, db, ctx.organization_id)
    invoice = await repo.get(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    res = InvoiceResponse.model_validate(invoice)
    await CacheService.set(cache_key, res.model_dump(), expire=TTL_INVOICE_DETAIL)
    return res


@router.post("/{invoice_id}/pay")
async def record_payment(
    invoice_id: str,
    amount: int,
    payment_method: str = "cash",
    reference_number: Optional[str] = None,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    service = InvoiceService(db, ctx.organization_id)
    res = await service.record_payment(invoice_id, amount, payment_method, reference_number)
    await InvalidateHelper.invalidate_invoice(ctx.organization_id, invoice_id)
    return res


@router.post("/{invoice_id}/approve")
async def approve_invoice(
    invoice_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    from app.database.models import PaymentProof, ProofStatus, InvoiceStatus
    import datetime
    from datetime import timezone

    # Find the invoice
    repo = BaseRepository(Invoice, db, ctx.organization_id)
    invoice = await repo.get(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn")

    # Find the pending proof
    query = select(PaymentProof).where(
        PaymentProof.invoice_id == invoice_id,
        PaymentProof.organization_id == ctx.organization_id,
        PaymentProof.status == ProofStatus.PENDING
    )
    result = await db.execute(query)
    proof = result.scalar_one_or_none()

    if not proof:
        raise HTTPException(status_code=400, detail="Không có minh chứng nào đang chờ duyệt")

    proof.status = ProofStatus.VERIFIED
    proof.verified_by = ctx.user.id
    proof.verified_at = datetime.datetime.now(timezone.utc)

    # Record payment full remaining amount
    service = InvoiceService(db, ctx.organization_id)
    remaining = invoice.total_amount - (invoice.paid_amount or 0)
    if remaining > 0:
        await service.record_payment(invoice_id, remaining, "BANK_TRANSFER", notes="Duyệt minh chứng từ khách thuê")
    else:
        invoice.status = InvoiceStatus.PAID

    await db.commit()
    await InvalidateHelper.invalidate_invoice(ctx.organization_id, invoice_id)
    return {"status": "success", "message": "Đã duyệt minh chứng và ghi nhận thanh toán"}


@router.post("/{invoice_id}/reject-proof")
async def reject_invoice_proof(
    invoice_id: str,
    reason: str = Query(...),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Reject payment proof and return invoice to active unpaid state"""
    from app.database.models import PaymentProof, ProofStatus, InvoiceStatus

    import datetime
    from datetime import timezone

    # Find the invoice
    repo = BaseRepository(Invoice, db, ctx.organization_id)
    invoice = await repo.get(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn")

    # Find the pending proof
    query = select(PaymentProof).where(
        PaymentProof.invoice_id == invoice_id,
        PaymentProof.organization_id == ctx.organization_id,
        PaymentProof.status == ProofStatus.PENDING
    )
    result = await db.execute(query)
    proof = result.scalar_one_or_none()

    if not proof:
        raise HTTPException(status_code=400, detail="Không có minh chứng nào đang chờ duyệt")

    # Update proof status to REJECTED
    proof.status = ProofStatus.REJECTED
    proof.verified_by = ctx.user.id
    proof.verified_at = datetime.datetime.now(timezone.utc)
    proof.note = f"Bị từ chối: {reason}"

    # Return invoice back to SENT (active unpaid)
    invoice.status = InvoiceStatus.SENT

    await db.commit()
    await InvalidateHelper.invalidate_invoice(ctx.organization_id, invoice_id)
    return {"status": "success", "message": f"Đã từ chối minh chứng. Lý do: {reason}"}


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: str,
    data: InvoiceCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    service = InvoiceService(db, ctx.organization_id)
    res = await service.update_invoice(invoice_id, data)
    await InvalidateHelper.invalidate_invoice(ctx.organization_id, invoice_id)
    return res


@router.post("/{invoice_id}/confirm", response_model=InvoiceResponse)
async def confirm_invoice(
    invoice_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    service = InvoiceService(db, ctx.organization_id)
    res = await service.confirm_invoice(invoice_id)
    await InvalidateHelper.invalidate_invoice(ctx.organization_id, invoice_id)
    return res
