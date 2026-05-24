import asyncio
from app.database.session import engine
from sqlalchemy import text

async def main():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id FROM invoices WHERE status = 'DRAFT' LIMIT 1"))
        row = res.fetchone()
        if row:
            print("INVOICE_ID:", row[0])
        else:
            print("No draft invoice")

asyncio.run(main())
