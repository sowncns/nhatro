"""Debug endpoint to check invoice visibility"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.models.models import Invoice

router = APIRouter()

@router.get("/debug/invoices")
async def debug_invoices(
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Debug endpoint to check invoice counts by status"""

    # Count all invoices
    total_result = await db.execute(
        select(func.count()).select_from(Invoice).where(
            Invoice.organization_id == ctx.organization_id
        )
    )
    total = total_result.scalar()

    # Count by status
    status_result = await db.execute(
        select(Invoice.status, func.count()).select_from(Invoice).where(
            Invoice.organization_id == ctx.organization_id
        ).group_by(Invoice.status)
    )
    by_status = {row[0]: row[1] for row in status_result.all()}

    # Count archived
    archived_result = await db.execute(
        select(func.count()).select_from(Invoice).where(
            Invoice.organization_id == ctx.organization_id,
            Invoice.archived_at != None
        )
    )
    archived = archived_result.scalar()

    # Get sample DRAFT invoices
    draft_result = await db.execute(
        select(Invoice).where(
            Invoice.organization_id == ctx.organization_id,
            Invoice.status == 'DRAFT'
        ).limit(5)
    )
    draft_samples = []
    for inv in draft_result.scalars().all():
        draft_samples.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "status": inv.status,
            "archived_at": str(inv.archived_at) if inv.archived_at else None,
            "billing_month": inv.billing_month,
            "billing_year": inv.billing_year,
        })

    return {
        "total_invoices": total,
        "by_status": by_status,
        "archived_count": archived,
        "draft_samples": draft_samples,
    }
