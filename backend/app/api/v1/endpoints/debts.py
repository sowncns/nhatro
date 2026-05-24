from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.core.deps import get_tenant_context, TenantContext
from app.schemas.schemas import DebtRecordResponse
from app.services.debt_query_service import DebtQueryService

router = APIRouter()


@router.get("", response_model=list[DebtRecordResponse])
async def list_debts(
    status: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    service = DebtQueryService(db, ctx.organization_id)
    items = await service.list(status=status, limit=limit)
    return [DebtRecordResponse.model_validate(x) for x in items]

