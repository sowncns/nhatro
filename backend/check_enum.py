import asyncio
import asyncpg
import os

async def main():
    import sys
    sys.path.append('.')
    from app.core.config import settings
    
    url = settings.DATABASE_URL
    if url.startswith('postgresql+asyncpg://'):
        url = url.replace('postgresql+asyncpg://', 'postgresql://')
        
    conn = await asyncpg.connect(url)
    
    types = await conn.fetch("SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE typname = 'invoicestatus';")
    for t in types:
        print(t['enumlabel'])
        
    await conn.close()

asyncio.run(main())
