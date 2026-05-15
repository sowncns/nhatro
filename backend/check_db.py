import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import sys

async def check():
    url = "postgresql+asyncpg://postgres:arneca0b18102005Ss@db.nebsjsmspuznpnucvcxj.supabase.co:5432/postgres"
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        try:
            res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'contracts' AND column_name = 'archived_at'"))
            col = res.scalar()
            if col:
                print("Column archived_at EXISTS")
            else:
                print("Column archived_at MISSING")
        except Exception as e:
            print(f"Error: {e}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
