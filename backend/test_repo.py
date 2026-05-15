import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database.models import Contract, ContractStatus
from app.repositories.base import BaseRepository
import sys

async def check():
    url = "postgresql+asyncpg://postgres:arneca0b18102005Ss@db.nebsjsmspuznpnucvcxj.supabase.co:5432/postgres"
    engine = create_async_engine(url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Need an organization_id. Let's try to get one from DB
            from sqlalchemy import text
            res = await db.execute(text("SELECT id FROM organizations LIMIT 1"))
            oid = res.scalar()
            if not oid:
                print("No organization found")
                return
            
            repo = BaseRepository(Contract, db, oid)
            items = await repo.get_all(limit=5, mode="active")
            print(f"Loaded {len(items)} active contracts")
        except Exception as e:
            import traceback
            traceback.print_exc()
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
