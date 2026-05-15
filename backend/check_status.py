import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    url = "postgresql+asyncpg://postgres:arneca0b18102005Ss@db.nebsjsmspuznpnucvcxj.supabase.co:5432/postgres"
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT status, actual_end_date FROM contracts WHERE contract_number = 'HD2026054612'"))
        row = res.one_or_none()
        print(f"STATUS: {row[0] if row else 'NOT FOUND'}")
        print(f"ACTUAL_END_DATE: {row[1] if row else 'N/A'}")
        
        if row:
            # Check invoices
            res = await conn.execute(text("SELECT id, billing_month, billing_year, status FROM invoices WHERE contract_id IN (SELECT id FROM contracts WHERE contract_number = 'HD2026054612')"))
            for inv in res.all():
                print(f"Invoice: {inv[0]} - {inv[1]}/{inv[2]} - {inv[3]}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
