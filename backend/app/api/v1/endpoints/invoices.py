"""Invoices Endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.models.models import Invoice
from app.schemas.schemas import InvoiceCreate, InvoiceResponse, PaginatedResponse
from app.repositories.base import BaseRepository
from app.services.invoice_service import InvoiceService

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
    return PaginatedResponse(
        items=[InvoiceResponse.model_validate(i) for i in items],
        total=total, page=page, size=size,
        pages=(total + size - 1) // size,
    )


@router.post("", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    data: InvoiceCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    service = InvoiceService(db, ctx.organization_id)
    return await service.create_invoice(data)


@router.post("/auto-generate")
async def auto_generate_invoices(
    billing_month: int,
    billing_year: int,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Auto-generate invoices for all occupied rooms"""
    from sqlalchemy import select
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
    return {"generated": generated, "errors": errors}


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    repo = BaseRepository(Invoice, db, ctx.organization_id)
    invoice = await repo.get(invoice_id)
    if not invoice:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceResponse.model_validate(invoice)


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
    return await service.record_payment(invoice_id, amount, payment_method, reference_number)


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: str,
    data: InvoiceCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    service = InvoiceService(db, ctx.organization_id)
    return await service.update_invoice(invoice_id, data)


@router.post("/{invoice_id}/confirm", response_model=InvoiceResponse)
async def confirm_invoice(
    invoice_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    service = InvoiceService(db, ctx.organization_id)
    return await service.confirm_invoice(invoice_id)
