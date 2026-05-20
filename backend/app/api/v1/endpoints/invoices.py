"""Invoices Endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.models.models import Invoice
from app.schemas.schemas import InvoiceCreate, InvoiceResponse, PaginatedResponse
from app.repositories.base import BaseRepository
from app.services.invoice_service import InvoiceService
from app.services.cache_service import CacheService
from app.services.invalidate_helper import InvalidateHelper
from app.core.cache_constants import TTL_INVOICE_LIST, TTL_INVOICE_DETAIL

router = APIRouter()


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
