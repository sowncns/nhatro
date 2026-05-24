import asyncio
from app.database.session import engine
from sqlalchemy import select, text
from app.database.models import Invoice

async def main():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id FROM invoices WHERE status = 'DRAFT' LIMIT 1"))
        row = res.fetchone()
        if not row:
            print("No draft invoice found.")
            return
        
        invoice_id = row[0]
        print(f"Trying to confirm {invoice_id}")

    from app.services.invoice_service import InvoiceService
    from app.database.session import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        # Get organization ID
        res = await db.execute(text(f"SELECT organization_id FROM invoices WHERE id = '{invoice_id}'"))
        org_id = res.scalar()
        
        service = InvoiceService(db, org_id)
        try:
            resp = await service.confirm_invoice(invoice_id)
            print("Success!", resp.model_dump())
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(main())
