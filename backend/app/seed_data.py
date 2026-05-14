"""
Seed Sample Data - Run this to populate database with demo data
Usage: python -m app.utils.seed_data
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.database.session import _database_url_and_connect_args
from app.core.security import hash_password
from app.models.models import (
    User, UserRole, Organization, SubscriptionPlan, OrganizationMember, OrgMemberRole,
    Subscription, FeatureEntitlement, SaaSPayment, SaaSPaymentStatus, SaaSPaymentType,
    BoardingHouse, Room, Tenant, RoomTenant, Contract,
    MeterReading, Invoice, InvoiceStatus, RoomStatus
)
from datetime import date, datetime, timezone, timedelta
import random
import uuid


async def seed():
    database_url, connect_args = _database_url_and_connect_args()
    engine = create_async_engine(database_url, echo=False, connect_args=connect_args)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("🌱 Seeding database...")

        existing_owner = await db.execute(select(User).where(User.email == "demo@nhatro.vn"))
        if existing_owner.scalar_one_or_none():
            print("✅ Demo data already exists, skipping duplicate seed.")
            print("\n📋 Demo credentials:")
            print("   Chủ trọ: demo@nhatro.vn / Demo@123456")
            print("   Admin hệ thống: admin@nhatro.vn / Admin@123456")
            return

        # Create platform admin user
        admin = User(
            id=str(uuid.uuid4()),
            email="admin@nhatro.vn",
            hashed_password=hash_password("Admin@123456"),
            full_name="Admin Hệ Thống",
            phone="0900000000",
            role=UserRole.PLATFORM_ADMIN,
            is_active=True,
            is_verified=True,
        )
        db.add(admin)

        # Create owner user
        owner = User(
            id=str(uuid.uuid4()),
            email="demo@nhatro.vn",
            hashed_password=hash_password("Demo@123456"),
            full_name="Nguyễn Văn An",
            phone="0901234567",
            role=UserRole.OWNER,
            is_active=True,
            is_verified=True,
        )
        db.add(owner)
        await db.flush()

        # Create organization
        org = Organization(
            id=str(uuid.uuid4()),
            name="Nhà Trọ Hoàng Gia",
            slug="nha-tro-hoang-gia",
            owner_id=owner.id,
            subscription_plan=SubscriptionPlan.PRO,
            address="123 Đường Nguyễn Trãi, Quận 1, TP.HCM",
            phone="0901234567",
            bank_name="Vietcombank",
            bank_account="0123456789",
            bank_account_name="NGUYEN VAN AN",
        )
        db.add(org)
        await db.flush()

        pro_payment = SaaSPayment(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            user_id=owner.id,
            payment_type=SaaSPaymentType.PLAN,
            status=SaaSPaymentStatus.PAID,
            plan=SubscriptionPlan.PRO,
            amount=399_000,
            provider="manual",
            reference_number="NHT-DEMO-PRO",
            checkout_url="/billing/checkout/NHT-DEMO-PRO",
            paid_at=datetime.now(timezone.utc),
            approved_by=admin.id,
        )
        db.add(pro_payment)
        await db.flush()

        db.add(
            Subscription(
                organization_id=org.id,
                plan=SubscriptionPlan.PRO,
                price=399_000,
                starts_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                is_active=True,
            )
        )

        for feature_key, name in [
            ("auto_invoice", "Tự động tạo hóa đơn hàng tháng"),
            ("bank_qr", "QR thanh toán ngân hàng"),
            ("contract_alert", "Cảnh báo hợp đồng sắp hết hạn"),
        ]:
            db.add(
                FeatureEntitlement(
                    organization_id=org.id,
                    feature_key=feature_key,
                    name=name,
                    source_payment_id=pro_payment.id,
                    expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                )
            )

        # Add owner as member
        db.add(OrganizationMember(
            organization_id=org.id,
            user_id=owner.id,
            role=OrgMemberRole.OWNER,
        ))

        # Create boarding houses
        bh1 = BoardingHouse(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            name="Khu A - Nguyễn Trãi",
            address="123 Đường Nguyễn Trãi, Quận 1, TP.HCM",
            description="Khu nhà trọ cao cấp, gần trung tâm",
            total_floors=4,
        )
        bh2 = BoardingHouse(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            name="Khu B - Lê Văn Sỹ",
            address="456 Đường Lê Văn Sỹ, Quận 3, TP.HCM",
            description="Khu nhà trọ tiện nghi, an ninh",
            total_floors=3,
        )
        db.add_all([bh1, bh2])
        await db.flush()

        # Create rooms
        rooms = []
        for floor in range(1, 5):
            for num in range(1, 6):
                status = random.choice([RoomStatus.OCCUPIED, RoomStatus.OCCUPIED, RoomStatus.AVAILABLE])
                room = Room(
                    id=str(uuid.uuid4()),
                    organization_id=org.id,
                    boarding_house_id=bh1.id,
                    room_number=f"A{floor}0{num}",
                    floor=floor,
                    area=random.uniform(18, 30),
                    max_occupants=2,
                    base_price=random.choice([3_500_000, 4_000_000, 4_500_000, 5_000_000]),
                    electricity_price=4_000,
                    water_price=15_000,
                    internet_fee=100_000,
                    parking_fee=150_000,
                    status=status,
                    amenities=["Máy lạnh", "Nóng lạnh", "Tủ lạnh"],
                )
                rooms.append(room)
                db.add(room)

        await db.flush()

        # Create tenants
        tenant_names = [
            "Trần Thị Bình", "Lê Văn Cường", "Phạm Thị Dung",
            "Hoàng Văn Em", "Ngô Thị Phúc", "Vũ Văn Giang",
            "Đặng Thị Hoa", "Bùi Văn Inh", "Dương Thị Kim",
            "Lý Văn Long",
        ]
        tenants = []
        for i, name in enumerate(tenant_names):
            tenant = Tenant(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                full_name=name,
                phone=f"09{random.randint(10000000, 99999999)}",
                email=f"tenant{i+1}@gmail.com",
                id_card=f"{random.randint(100000000000, 999999999999)}",
                permanent_address="Hà Nội",
            )
            tenants.append(tenant)
            db.add(tenant)

        await db.flush()

        # Create contracts for occupied rooms
        now = date.today()
        occupied_rooms = [r for r in rooms if r.status == RoomStatus.OCCUPIED]
        for i, room in enumerate(occupied_rooms[:len(tenants)]):
            tenant = tenants[i % len(tenants)]
            contract = Contract(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                room_id=room.id,
                tenant_id=tenant.id,
                contract_number=f"HD2024{i+1:04d}",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31),
                monthly_rent=room.base_price,
                deposit_amount=room.base_price * 2,
                deposit_paid=True,
                payment_due_day=5,
                status="active",
            )
            db.add(contract)

            # Room tenant record
            db.add(RoomTenant(
                organization_id=org.id,
                room_id=room.id,
                tenant_id=tenant.id,
                is_primary=True,
                move_in_date=date(2024, 1, 1),
            ))

        await db.flush()

        # Create meter readings and invoices for last 3 months
        for room in occupied_rooms[:8]:
            elec_prev = random.uniform(100, 500)
            water_prev = random.uniform(10, 50)
            for month_offset in range(3, 0, -1):
                month = ((now.month - month_offset - 1) % 12) + 1
                year = now.year if now.month - month_offset > 0 else now.year - 1
                elec_curr = elec_prev + random.uniform(50, 200)
                water_curr = water_prev + random.uniform(5, 20)

                reading = MeterReading(
                    organization_id=org.id,
                    room_id=room.id,
                    reading_month=month,
                    reading_year=year,
                    electricity_previous=elec_prev,
                    electricity_current=elec_curr,
                    electricity_usage=elec_curr - elec_prev,
                    water_previous=water_prev,
                    water_current=water_curr,
                    water_usage=water_curr - water_prev,
                    recorded_by=owner.id,
                )
                db.add(reading)

                elec_amount = int((elec_curr - elec_prev) * room.electricity_price)
                water_amount = int((water_curr - water_prev) * room.water_price)
                total = room.base_price + elec_amount + water_amount + room.internet_fee + room.parking_fee

                invoice = Invoice(
                    organization_id=org.id,
                    room_id=room.id,
                    invoice_number=f"HD{year}{month:02d}{room.room_number}",
                    billing_month=month,
                    billing_year=year,
                    due_date=date(year, month, 5),
                    rent_amount=room.base_price,
                    electricity_amount=elec_amount,
                    water_amount=water_amount,
                    internet_amount=room.internet_fee,
                    parking_amount=room.parking_fee,
                    total_amount=total,
                    paid_amount=total if month_offset > 1 else 0,
                    status=InvoiceStatus.PAID if month_offset > 1 else InvoiceStatus.SENT,
                )
                db.add(invoice)
                elec_prev = elec_curr
                water_prev = water_curr

        await db.commit()
        print("✅ Seed complete!")
        print("\n📋 Demo credentials:")
        print("   Chủ trọ: demo@nhatro.vn / Demo@123456")
        print("   Admin hệ thống: admin@nhatro.vn / Admin@123456")
        print(f"\n   Organization: Nhà Trọ Hoàng Gia")
        print(f"   Rooms: {len(rooms)}")
        print(f"   Tenants: {len(tenants)}")


if __name__ == "__main__":
    asyncio.run(seed())
