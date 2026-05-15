import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    url = "postgresql+asyncpg://postgres:arneca0b18102005Ss@db.nebsjsmspuznpnucvcxj.supabase.co:5432/postgres"
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT status, count(*) FROM contracts GROUP BY status"))
        for row in res.all():
            print(f"Status: {row[0]} - Count: {row[1]}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
