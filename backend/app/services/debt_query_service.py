from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import DebtRecord


class DebtQueryService:
    def __init__(self, db: AsyncSession, organization_id: str):
        self.db = db
        self.organization_id = organization_id

    async def list(self, status: str | None = None, limit: int = 100):
        q = select(DebtRecord).where(DebtRecord.organization_id == self.organization_id).order_by(DebtRecord.created_at.desc()).limit(limit)
        if status:
            q = q.where(DebtRecord.status == status)
        res = await self.db.execute(q)
        return res.scalars().all()

    async def get(self, debt_id: str):
        obj = await self.db.get(DebtRecord, debt_id)
        if not obj or str(obj.organization_id) != str(self.organization_id):
            raise HTTPException(status_code=404, detail="Debt record not found")
        return obj

