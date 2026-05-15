import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    url = "postgresql+asyncpg://postgres:arneca0b18102005Ss@db.nebsjsmspuznpnucvcxj.supabase.co:5432/postgres"
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT room_number, parking_fee, base_price FROM rooms"))
        for row in res.all():
            print(f"Room: {row[0]} | parking_fee: {row[1]} | base_price: {row[2]}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
