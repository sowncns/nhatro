from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.schemas.schemas import TenantOTPSendRequest
from app.database.models import Tenant, Contract
from app.core.security import create_access_token
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/login")
async def login(
    data: TenantOTPSendRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login without OTP - just email or phone to get access token"""
    try:
        if not data.email and not data.phone:
            raise HTTPException(status_code=400, detail="Email hoặc Số điện thoại là bắt buộc")

        # Check if tenant exists
        query = select(Tenant)
        if data.email:
            query = query.where(Tenant.email == data.email)
        elif data.phone:
            query = query.where(Tenant.phone == data.phone)
        
        result = await db.execute(query)
        tenant = result.scalars().first()
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Không tìm thấy người thuê với thông tin này")

        # Generate JWT token directly
        access_token = create_access_token(data={"sub": str(tenant.id), "role": "tenant"})
        
        # Check if multiple contracts
        contract_query = select(Contract).where(
            Contract.tenant_id == tenant.id,
            Contract.status == "ACTIVE"
        )
        contract_result = await db.execute(contract_query)
        contracts = contract_result.scalars().all()
        
        requires_room_selection = len(contracts) > 1

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "requires_room_selection": requires_room_selection,
            "tenant_id": tenant.id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
