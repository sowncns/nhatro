import asyncio
from app.database.session import engine
from app.database.models import DebtRecord, Base

async def main():
    async with engine.begin() as conn:
        try:
            await conn.run_sync(DebtRecord.__table__.create)
            print("Created debt_records")
        except Exception as e:
            print(f"Error creating debt_records: {e}")

asyncio.run(main())
