import asyncio
from app.database.session import engine
from app.database.models import Base

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Done")

asyncio.run(main())
