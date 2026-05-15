import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import sys

async def check():
    url = "postgresql+asyncpg://postgres:arneca0b18102005Ss@db.nebsjsmspuznpnucvcxj.supabase.co:5432/postgres"
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        try:
            res = await conn.execute(text("SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE pg_type.typname = 'contractstatus'"))
            rows = res.all()
            print("Enum labels in DB:")
            for row in rows:
                print(f"- {row[0]}")
        except Exception as e:
            print(f"Error: {e}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
