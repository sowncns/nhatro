import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import sys

async def check():
    url = "postgresql+asyncpg://postgres:arneca0b18102005Ss@db.nebsjsmspuznpnucvcxj.supabase.co:5432/postgres"
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        try:
            res = await conn.execute(text("SELECT id, status, archived_at FROM contracts"))
            rows = res.all()
            for row in rows:
                print(f"ID: {row[0]}, Status: {row[1]}, ArchivedAt: {row[2]}")
        except Exception as e:
            print(f"Error: {e}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
