import asyncio
import uuid
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.contract_termination_service import ContractTerminationService
from app.schemas.schemas import ContractTerminateRequest, DepositDeduction

async def test_termination():
    url = "postgresql+asyncpg://postgres:arneca0b18102005Ss@db.nebsjsmspuznpnucvcxj.supabase.co:5432/postgres"
    engine = create_async_engine(url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Use the org and user from the context (cb688075-55c5-4b41-b12a-1160823617a1)
    org_id = "cb688075-55c5-4b41-b12a-1160823617a1"
    user_id = "8409090a-1191-4cf1-8319-387063f9b2f6"
    
    # Contract HD2026054612 ID (from screenshot/previous check)
    # I need to find the ID of HD2026054612
    
    async with async_session() as session:
        from sqlalchemy import text
        res = await session.execute(text("SELECT id FROM contracts WHERE contract_number = 'HD2026054612'"))
        contract_id = res.scalar()
        print(f"Contract ID: {contract_id}")
        
        if not contract_id:
            print("Contract not found")
            return

        service = ContractTerminationService(session, org_id, user_id)
        
        data = ContractTerminateRequest(
            actual_end_date=date(2026, 5, 15),
            final_electricity=120,
            final_water=12,
            refund_amount=0,
            move_out_reason="Hết hạn hợp đồng",
            termination_note="ko",
            deposit_deductions=[
                DepositDeduction(reason="f", amount=1200)
            ]
        )
        
        try:
            print("Attempting termination...")
            contract = await service.terminate_contract(contract_id, data)
            await session.commit()
            print("Termination successful!")
        except Exception as e:
            print(f"TERMINATION FAILED: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_termination())
