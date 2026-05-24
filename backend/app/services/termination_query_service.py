from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import TerminationHistory


class TerminationQueryService:
    def __init__(self, db: AsyncSession, organization_id: str):
        self.db = db
        self.organization_id = organization_id

    async def list_for_contract(self, contract_id: str, limit: int = 50):
        res = await self.db.execute(
            select(TerminationHistory)
            .where(
                TerminationHistory.organization_id == self.organization_id,
                TerminationHistory.contract_id == contract_id,
            )
            .order_by(TerminationHistory.created_at.desc())
            .limit(limit)
        )
        return res.scalars().all()

    async def get(self, history_id: str):
        obj = await self.db.get(TerminationHistory, history_id)
        if not obj or str(obj.organization_id) != str(self.organization_id):
            raise HTTPException(status_code=404, detail="Termination history not found")
        return obj

