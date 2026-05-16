from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.api.deps import get_portal_tenant_context, PortalTenantContext
from app.database.models import Contract, Invoice, Room, Complaint, RepairRequest
from app.schemas.schemas import ComplaintCreate, RepairRequestCreate
from sqlalchemy import select

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
    # Get invoices for the tenant's active contracts
    from sqlalchemy.orm import joinedload
    query = select(Invoice).options(joinedload(Invoice.contract)).where(
        Invoice.contract_id.in_(ctx.contract_ids)
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
            "representative_name": inv.contract.representative_name if inv.contract else "N/A"
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
    query = select(Invoice).where(
        Invoice.id == invoice_id,
        Invoice.contract_id.in_(ctx.contract_ids)
    )
    result = await db.execute(query)
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn hoặc bạn không có quyền xem")
        
    return invoice

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
async def upload_payment_proof(
    invoice_id: str,
    file: UploadFile = File(...),
    ctx: PortalTenantContext = Depends(get_portal_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    # Validate invoice belongs to tenant's contracts
    invoice_result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = invoice_result.scalar_one_or_none()
    
    if not invoice or str(invoice.contract_id) not in ctx.contract_ids:
        raise HTTPException(status_code=403, detail="Bạn không có quyền upload minh chứng cho hóa đơn này")
        
    # Save file
    from app.services.upload_service import UploadService
    upload_service = UploadService()
    file_path = await upload_service.save_file(file, subfolder="proofs")
    
    # Create PaymentProof record
    from app.database.models import PaymentProof
    proof = PaymentProof(
        organization_id=invoice.organization_id,
        invoice_id=invoice_id,
        image_url=file_path,
        status="pending"
    )
    db.add(proof)
    
    # Update Invoice status to WAITING_VERIFY
    invoice.status = "WAITING_VERIFY"
    
    await db.flush()
    return {"message": "Đã upload minh chứng thành công", "url": file_path}


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
