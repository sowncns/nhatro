import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

if "?sslmode=" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?sslmode=")[0]

engine = create_async_engine(DATABASE_URL)

async def main():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE contracts ADD COLUMN member_ids JSON DEFAULT '[]'::json;"))
            print("Successfully added member_ids to contracts table")
        except Exception as e:
            print(f"Error (maybe column already exists): {e}")

if __name__ == "__main__":
    asyncio.run(main())
