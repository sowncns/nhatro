import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import sys

async def check():
    url = "postgresql+asyncpg://postgres:arneca0b18102005Ss@db.nebsjsmspuznpnucvcxj.supabase.co:5432/postgres"
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        try:
            # Get room id for '102'
            res = await conn.execute(text("SELECT id FROM rooms WHERE room_number = '102'"))
            room_id = res.scalar()
            print(f"Room 102 ID: {room_id}")
            
            if room_id:
                res = await conn.execute(text(f"SELECT id, billing_month, billing_year FROM invoices WHERE room_id = '{room_id}'"))
                rows = res.all()
                print("Invoices for Room 102:")
                for row in rows:
                    print(f"- ID: {row[0]}, Period: {row[1]}/{row[2]}")
        except Exception as e:
            print(f"Error: {e}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
