import httpx
import asyncio

async def test():
    # We need a valid token. Since we don't have one easily, 
    # we can try to call the internal repository logic again with specific organization IDs.
    pass

if __name__ == "__main__":
    # Instead of httpx, let's just use the repository check with ALL known org IDs.
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.database.models import Contract
    from app.repositories.base import BaseRepository
    from sqlalchemy import text

    async def check():
        url = "postgresql+asyncpg://postgres:arneca0b18102005Ss@db.nebsjsmspuznpnucvcxj.supabase.co:5432/postgres"
        engine = create_async_engine(url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as db:
            res = await db.execute(text("SELECT id FROM organizations"))
            orgs = res.scalars().all()
            for oid in orgs:
                repo = BaseRepository(Contract, db, oid)
                items = await repo.get_all(mode="active")
                print(f"Org {oid}: Found {len(items)} active contracts")
        await engine.dispose()

    asyncio.run(check())
