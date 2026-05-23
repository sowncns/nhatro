from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.api.deps import get_portal_tenant_context, PortalTenantContext
from app.database.models import Contract, Invoice, Room, Complaint, RepairRequest, Organization, Payment, PaymentMethod, InvoiceStatus
from app.schemas.schemas import ComplaintCreate, RepairRequestCreate
from sqlalchemy import select
from app.services.vietqr_service import vietqr_service
from datetime import datetime

router = APIRouter()

@router.get("/rooms")
async def get_tenant_rooms(
    ctx: PortalTenantContext = Depends(get_portal_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    # Get rooms associated with the tenant's active contracts
    query = select(Room).join(Contract, Contract.room_id == Room.id).where(
        Contract.id.in_(ctx.contract_ids)
    )
    result = await db.execute(query)
    rooms = result.scalars().all()
    return rooms

@router.get("/invoices")
async def get_tenant_invoices(
    ctx: PortalTenantContext = Depends(get_portal_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    # Get invoices for the tenant's active contracts OR any unpaid invoices of their other contracts
    from sqlalchemy.orm import joinedload
    from sqlalchemy import or_
    
    query = select(Invoice).join(Contract, Invoice.contract_id == Contract.id).options(
        joinedload(Invoice.contract)
    ).where(
        Contract.tenant_id == ctx.tenant_id,
        or_(
            Contract.status == "ACTIVE",
            Invoice.status.notin_([InvoiceStatus.PAID, InvoiceStatus.CANCELLED, InvoiceStatus.DRAFT, "PAID", "CANCELLED", "DRAFT"])
        )
    )
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    return [
        {
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "billing_month": inv.billing_month,
            "billing_year": inv.billing_year,
            "due_date": inv.due_date,
            "total_amount": inv.total_amount,
            "status": inv.status,
            "room_id": inv.room_id,
            "contract_id": inv.contract_id
        }
        for inv in invoices
    ]


@router.get("/contracts")
async def get_tenant_contracts(
    ctx: PortalTenantContext = Depends(get_portal_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    query = select(Contract).where(
        Contract.id.in_(ctx.contract_ids)
    )
    result = await db.execute(query)
    contracts = result.scalars().all()
    return contracts


@router.get("/invoices/{invoice_id}")
async def get_tenant_invoice(
    invoice_id: str,
    ctx: PortalTenantContext = Depends(get_portal_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    """Get invoice detail with VietQR payment code"""
    from sqlalchemy.orm import joinedload
    from sqlalchemy import or_

    query = select(Invoice).join(Contract, Invoice.contract_id == Contract.id).options(
        joinedload(Invoice.contract)
    ).where(
        Invoice.id == invoice_id,
        Contract.tenant_id == ctx.tenant_id,
        or_(
            Contract.status == "ACTIVE",
            Invoice.status.notin_([InvoiceStatus.PAID, InvoiceStatus.CANCELLED, InvoiceStatus.DRAFT, "PAID", "CANCELLED", "DRAFT"])
        )
    )
    result = await db.execute(query)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn hoặc bạn không có quyền xem")

    # Get organization info for bank details
    org_query = select(Organization).where(Organization.id == invoice.contract.organization_id)
    org_result = await db.execute(org_query)
    org = org_result.scalar_one_or_none()

    # Generate VietQR code
    qr_url = None
    bank_info = None

    if org and org.bank_account:
        bank_code = vietqr_service.get_bank_code(org.bank_name or "vietcombank")
        qr_url = vietqr_service.generate_qr_url(
            bank_code=bank_code,
            account_number=org.bank_account,
            amount=invoice.total_amount,
            description=f"THANHTOAN {invoice.invoice_number}",
            account_name=org.bank_account_name
        )

        bank_info = {
            "bank_name": org.bank_name or "Vietcombank",
            "account_number": org.bank_account,
            "account_name": org.bank_account_name or org.name,
            "amount": invoice.total_amount,
            "content": f"THANHTOAN {invoice.invoice_number}"
        }

    return {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "billing_month": invoice.billing_month,
        "billing_year": invoice.billing_year,
        "due_date": invoice.due_date,
        "total_amount": invoice.total_amount,
        "status": invoice.status,
        "rent_amount": invoice.rent_amount,
        "electricity_amount": invoice.electricity_amount,
        "water_amount": invoice.water_amount,
        "internet_amount": invoice.internet_amount,
        "parking_amount": invoice.parking_amount,
        "other_amount": invoice.other_amount,
        "notes": invoice.notes,
        "qr_code_url": qr_url,
        "bank_info": bank_info,
        "contract": {
            "id": invoice.contract.id,
            "room_id": invoice.contract.room_id
        } if invoice.contract else None
    }


@router.post("/invoices/{invoice_id}/payment-proof")
async def upload_payment_proof_v2(
    invoice_id: str,
    proof_image: UploadFile = File(...),
    ctx: PortalTenantContext = Depends(get_portal_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    """Upload payment proof image using PaymentProof as single source of truth."""
    from sqlalchemy.orm import joinedload
    from sqlalchemy import or_
    from app.database.models import PaymentProof, ProofStatus, InvoiceStatus

    query = select(Invoice).join(Contract, Invoice.contract_id == Contract.id).options(
        joinedload(Invoice.contract)
    ).where(
        Invoice.id == invoice_id,
        Contract.tenant_id == ctx.tenant_id,
        or_(
            Contract.status == "ACTIVE",
            Invoice.status.notin_([InvoiceStatus.PAID, InvoiceStatus.CANCELLED, InvoiceStatus.DRAFT, "PAID", "CANCELLED", "DRAFT"])
        )
    )
    result = await db.execute(query)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn")

    if invoice.status in [InvoiceStatus.PAID, "PAID", "paid"]:
        raise HTTPException(status_code=400, detail="Hóa đơn đã được thanh toán")

    # Save proof image locally
    from app.services.upload_service import UploadService
    upload_service = UploadService()
    try:
        file_path = await upload_service.save_file(proof_image, subfolder="proofs")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể lưu file local: {str(e)}")

    # Reject duplicate pending proofs
    existing_result = await db.execute(
        select(PaymentProof).where(
            PaymentProof.invoice_id == invoice.id,
            PaymentProof.status == ProofStatus.PENDING
        )
    )
    existing_proof = existing_result.scalar_one_or_none()
    if existing_proof:
        raise HTTPException(status_code=400, detail="Hóa đơn này đang chờ chủ trọ duyệt minh chứng")

    proof = PaymentProof(
        organization_id=invoice.organization_id,
        invoice_id=invoice.id,
        image_url=file_path,
        status=ProofStatus.PENDING,
    )
    db.add(proof)

    invoice.status = InvoiceStatus.WAITING_VERIFY

    await db.commit()
    await db.refresh(proof)

    return {
        "message": "Đã upload minh chứng thành công. Chờ chủ trọ xác nhận.",
        "proof_id": proof.id,
        "proof_image_url": file_path,
        "invoice_status": "WAITING_VERIFY"
    }


@router.post("/complaints")
async def create_complaint(
    data: ComplaintCreate,
    ctx: PortalTenantContext = Depends(get_portal_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    if data.contract_id not in ctx.contract_ids:
        raise HTTPException(status_code=403, detail="Bạn không có quyền gửi khiếu nại cho hợp đồng này")
        
    # Get organization_id from contract
    contract_result = await db.execute(select(Contract).where(Contract.id == data.contract_id))
    contract = contract_result.scalar_one_or_none()
    
    complaint = Complaint(
        organization_id=contract.organization_id,
        contract_id=data.contract_id,
        title=data.title,
        description=data.description,
        status="pending"
    )
    db.add(complaint)
    await db.flush()
    return {"message": "Đã gửi khiếu nại thành công", "id": complaint.id}

@router.post("/repair-requests")
async def create_repair_request(
    data: RepairRequestCreate,
    ctx: PortalTenantContext = Depends(get_portal_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    if data.contract_id not in ctx.contract_ids:
        raise HTTPException(status_code=403, detail="Bạn không có quyền gửi yêu cầu sửa chữa cho hợp đồng này")
        
    # Get organization_id from contract
    contract_result = await db.execute(select(Contract).where(Contract.id == data.contract_id))
    contract = contract_result.scalar_one_or_none()
    
    repair_request = RepairRequest(
        organization_id=contract.organization_id,
        contract_id=data.contract_id,
        title=data.title,
        description=data.description,
        status="pending"
    )
    db.add(repair_request)
    await db.flush()
    return {"message": "Đã gửi yêu cầu sửa chữa thành công", "id": repair_request.id}


@router.post("/invoices/{invoice_id}/proof")
async def upload_payment_proof_legacy(
    invoice_id: str,
    file: UploadFile = File(...),
    ctx: PortalTenantContext = Depends(get_portal_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    """Legacy alias for frontend compatibility. Delegates to payment-proof flow."""
    return await upload_payment_proof_v2(
        invoice_id=invoice_id,
        proof_image=file,
        ctx=ctx,
        db=db,
    )


@router.post("/repair-requests/{request_id}/images")
async def upload_repair_image(
    request_id: str,
    file: UploadFile = File(...),
    ctx: PortalTenantContext = Depends(get_portal_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    # Validate request belongs to tenant
    result = await db.execute(select(RepairRequest).where(RepairRequest.id == request_id))
    req = result.scalar_one_or_none()
    
    if not req or str(req.contract_id) not in ctx.contract_ids:
        raise HTTPException(status_code=403, detail="Bạn không có quyền upload ảnh cho yêu cầu này")
        
    # Save file
    from app.services.upload_service import UploadService
    upload_service = UploadService()
    file_path = await upload_service.save_file(file, subfolder="repairs")
    
    # Create RepairRequestImage record
    from app.database.models import RepairRequestImage
    img = RepairRequestImage(
        repair_request_id=request_id,
        image_url=file_path
    )
    db.add(img)
    await db.flush()
    return {"message": "Đã upload ảnh thành công", "url": file_path}
