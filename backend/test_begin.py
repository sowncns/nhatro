import asyncio
from app.database.session import engine
from sqlalchemy import text
from app.database.models import Base

async def main():
    async with engine.begin() as conn:
        print("Begin block started!")
        await conn.execute(text("SELECT 1"))
        print("Query executed!")

asyncio.run(main())
