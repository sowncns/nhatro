import asyncio
from sqlalchemy import select
from app.database.session import engine, AsyncSessionLocal
from app.models.models import Room, RoomStatus, Organization, Contract
from app.services.invoice_service import InvoiceService
from app.schemas.schemas import InvoiceCreate
import datetime

async def main():
    async with AsyncSessionLocal() as db:
        orgs = await db.execute(select(Organization))
        org = orgs.scalars().first()
        if not org:
            print("No org")
            return
            
        print(f"Org: {org.id}")
        
        rooms = await db.execute(select(Room).where(Room.organization_id == org.id, Room.status == RoomStatus.OCCUPIED))
        room = rooms.scalars().first()
        if not room:
            print("No occupied rooms")
            return
            
        print(f"Testing room: {room.room_number}")
        
        contracts = await db.execute(select(Contract).where(Contract.room_id == room.id, Contract.status == "active"))
        contract = contracts.scalars().first()
        
        service = InvoiceService(db, org.id)

        try:
            print("Testing manual generate...")
            data = InvoiceCreate(
                room_id=room.id,
                billing_month=6,
                billing_year=2026,
                rent_amount=5000000,
                due_date=datetime.date.today(),
            )
            inv = await service.create_invoice(data, contract_id=contract.id if contract else None)
            print("Manual generate Success!", inv.invoice_number)
        except Exception as e:
            print(f"Manual generate Failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
