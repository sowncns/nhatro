import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    url = "postgresql+asyncpg://postgres:arneca0b18102005Ss@db.nebsjsmspuznpnucvcxj.supabase.co:5432/postgres"
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        # Get count of active contracts for the user's org
        org_id = "cb688075-55c5-4b41-b12a-1160823617a1"
        res = await conn.execute(text(f"SELECT count(*) FROM contracts WHERE organization_id = '{org_id}' AND status IN ('ACTIVE', 'DRAFT')"))
        print(f"Active Contracts Count: {res.scalar()}")
        
        res = await conn.execute(text(f"SELECT id, status FROM contracts WHERE organization_id = '{org_id}'"))
        for row in res.all():
            print(f"- {row[0]}: {row[1]}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
