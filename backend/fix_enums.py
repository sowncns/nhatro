import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import sys

async def fix_enums():
    url = "postgresql+asyncpg://postgres:arneca0b18102005Ss@db.nebsjsmspuznpnucvcxj.supabase.co:5432/postgres"
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        try:
            # We need to run these outside of a transaction if possible, or handle IF NOT EXISTS
            # Asyncpg connection usually handles this but let's be careful.
            
            # For ContractStatus
            for val in ['DRAFT', 'ENDED', 'CANCELLED', 'EXPIRED', 'TERMINATED']:
                try:
                    await conn.execute(text(f"ALTER TYPE contractstatus ADD VALUE IF NOT EXISTS '{val}'"))
                    await conn.commit()
                except Exception as e:
                    print(f"Skipping {val} for contractstatus: {e}")
            
            # For InvoiceStatus
            for val in ['DRAFT', 'SENT', 'PAID', 'OVERDUE', 'CANCELLED']:
                try:
                    await conn.execute(text(f"ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS '{val}'"))
                    await conn.commit()
                except Exception as e:
                    print(f"Skipping {val} for invoicestatus: {e}")

            # For MaintenanceStatus
            for val in ['PENDING', 'IN_PROGRESS', 'RESOLVED', 'CANCELLED']:
                try:
                    await conn.execute(text(f"ALTER TYPE maintenancestatus ADD VALUE IF NOT EXISTS '{val}'"))
                    await conn.commit()
                except Exception as e:
                    print(f"Skipping {val} for maintenancestatus: {e}")
                    
            print("Enums fixed")
        except Exception as e:
            print(f"Error: {e}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_enums())
