"""
SQLAlchemy ORM Models - Multi-tenant SaaS NhaTro (IMPROVED VERSION)
- Added consistent soft delete with mixins
- Added database constraints
- Improved indexes
- Better transaction handling support
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, Enum, JSON, Date, BigInteger, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func
import enum

from app.database.mixins import SoftDeleteMixin, TimestampMixin


class Base(DeclarativeBase):
    pass


def gen_uuid():
    return str(uuid.uuid4())


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class UserRole(str, enum.Enum):
    PLATFORM_ADMIN = "platform_admin"
    OWNER = "owner"
    MANAGER = "manager"
    TENANT = "tenant"

class OrgMemberRole(str, enum.Enum):
    OWNER = "owner"
    MANAGER = "manager"
    STAFF = "staff"

class SubscriptionPlan(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    BASIC = "basic"
    PRO = "pro"
    SCALE = "scale"

class SaaSPaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RepairStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"

class ComplaintStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"

class ProofStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class SaaSPaymentType(str, enum.Enum):
    PLAN = "plan"
    MODULE = "module"

class RoomStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"

class ContractStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    TERMINATED = "TERMINATED"

class DepositAction(str, enum.Enum):
    REFUND = "REFUND"
    DEDUCTION = "DEDUCTION"
    TRANSFER = "TRANSFER"

class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"
    WAITING_VERIFY = "WAITING_VERIFY"
    REJECTED = "REJECTED"

class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    MOMO = "MOMO"
    VNPAY = "VNPAY"

class MaintenanceStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"

class ReadingType(str, enum.Enum):
    MOVE_IN = "MOVE_IN"
    MONTHLY = "MONTHLY"
    MOVE_OUT = "MOVE_OUT"
    FINAL = "FINAL"

class NotificationType(str, enum.Enum):
    INVOICE_DUE = "invoice_due"
    CONTRACT_EXPIRY = "contract_expiry"
    MAINTENANCE_UPDATE = "maintenance_update"
    PAYMENT_RECEIVED = "payment_received"
    SYSTEM = "system"


# ─────────────────────────────────────────────
# CORE TABLES
# ─────────────────────────────────────────────

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20))
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.OWNER, nullable=False)

    # Relations
    organizations = relationship("Organization", back_populates="owner")
    org_memberships = relationship("OrganizationMember", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")

    __table_args__ = (
        CheckConstraint("email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$'", name="valid_email"),
        CheckConstraint("length(full_name) >= 2", name="valid_full_name"),
    )


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    owner_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    subscription_plan = Column(Enum(SubscriptionPlan), default=SubscriptionPlan.FREE, nullable=False)
    logo_url = Column(String(500))
    address = Column(String(500))
    phone = Column(String(20))
    bank_name = Column(String(100))
    bank_account = Column(String(50))
    bank_account_name = Column(String(100))
    settings = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relations
    owner = relationship("User", back_populates="organizations")
    members = relationship("OrganizationMember", back_populates="organization")
    boarding_houses = relationship("BoardingHouse", back_populates="organization")
    subscriptions = relationship("Subscription", back_populates="organization")
    feature_entitlements = relationship("FeatureEntitlement", back_populates="organization")
    saas_payments = relationship("SaaSPayment", back_populates="organization")

    __table_args__ = (
        CheckConstraint("length(name) >= 2", name="valid_org_name"),
        CheckConstraint("length(slug) >= 2", name="valid_slug"),
    )


class OrganizationMember(Base, TimestampMixin):
    __tablename__ = "organization_members"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    role = Column(Enum(OrgMemberRole), default=OrgMemberRole.STAFF, nullable=False)
    permissions = Column(JSON, default=list)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="org_memberships")

    __table_args__ = (
        Index("ix_org_members_org_user", "organization_id", "user_id", unique=True),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_tokens_user_active", "user_id", "is_revoked", "expires_at"),
    )


# ─────────────────────────────────────────────
# BUSINESS TABLES (all have organization_id + soft delete)
# ─────────────────────────────────────────────

class BoardingHouse(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "boarding_houses"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=False)
    description = Column(Text)
    images = Column(JSON, default=list)
    total_floors = Column(Integer, default=1)
    is_active = Column(Boolean, default=True, nullable=False)

    organization = relationship("Organization", back_populates="boarding_houses")
    rooms = relationship("Room", back_populates="boarding_house")

    __table_args__ = (
        CheckConstraint("total_floors > 0", name="positive_floors"),
        CheckConstraint("length(name) >= 2", name="valid_house_name"),
    )


class Room(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "rooms"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    boarding_house_id = Column(UUID(as_uuid=False), ForeignKey("boarding_houses.id"), nullable=False, index=True)
    room_number = Column(String(20), nullable=False)
    floor = Column(Integer, default=1)
    area = Column(Float)  # m2
    max_occupants = Column(Integer, default=2)
    base_price = Column(BigInteger, nullable=False)  # VND
    electricity_price = Column(BigInteger, default=4000)  # per kWh
    water_price = Column(BigInteger, default=15000)  # per m3
    internet_fee = Column(BigInteger, default=0)
    parking_fee = Column(BigInteger, default=0)
    status = Column(Enum(RoomStatus), default=RoomStatus.AVAILABLE, nullable=False)
    amenities = Column(JSON, default=list)
    images = Column(JSON, default=list)
    notes = Column(Text)

    organization = relationship("Organization")
    boarding_house = relationship("BoardingHouse", back_populates="rooms")
    tenants = relationship("RoomTenant", back_populates="room")
    contracts = relationship("Contract", back_populates="room")
    meter_readings = relationship("MeterReading", back_populates="room")
    invoices = relationship("Invoice", back_populates="room")
    maintenance_requests = relationship("MaintenanceRequest", back_populates="room")

    __table_args__ = (
        Index("ix_rooms_boarding_house_status", "boarding_house_id", "status"),
        Index("ix_rooms_org_status", "organization_id", "status", "is_archived"),
        CheckConstraint("base_price >= 0", name="positive_base_price"),
        CheckConstraint("electricity_price >= 0", name="positive_electricity_price"),
        CheckConstraint("water_price >= 0", name="positive_water_price"),
        CheckConstraint("max_occupants > 0", name="positive_max_occupants"),
        CheckConstraint("area IS NULL OR area > 0", name="positive_area"),
    )


class Tenant(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255))
    id_card = Column(String(20), unique=True)  # CCCD
    id_card_images = Column(JSON, default=list)
    date_of_birth = Column(Date)
    permanent_address = Column(String(500))
    avatar_url = Column(String(500))
    emergency_contact_name = Column(String(255))
    emergency_contact_phone = Column(String(20))
    notes = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)

    organization = relationship("Organization")
    room_tenants = relationship("RoomTenant", back_populates="tenant")
    contracts = relationship("Contract", back_populates="tenant")

    __table_args__ = (
        Index("ix_tenants_org_active", "organization_id", "is_active", "is_archived"),
        CheckConstraint("length(full_name) >= 2", name="valid_tenant_name"),
        CheckConstraint("length(phone) >= 10", name="valid_phone"),
    )


class RoomTenant(Base, SoftDeleteMixin):
    """Many-to-many: multiple tenants can share a room"""
    __tablename__ = "room_tenants"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    room_id = Column(UUID(as_uuid=False), ForeignKey("rooms.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    move_in_date = Column(Date, nullable=False)
    move_out_date = Column(Date)
    move_out_reason = Column(String(500))
    is_active = Column(Boolean, default=True, nullable=False)

    room = relationship("Room", back_populates="tenants")
    tenant = relationship("Tenant", back_populates="room_tenants")

    __table_args__ = (
        Index("ix_room_tenants_room_active", "room_id", "is_active"),
        Index("ix_room_tenants_tenant_active", "tenant_id", "is_active"),
        CheckConstraint("move_out_date IS NULL OR move_out_date >= move_in_date", name="valid_date_range"),
    )


class Contract(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    room_id = Column(UUID(as_uuid=False), ForeignKey("rooms.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True)
    contract_number = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    monthly_rent = Column(BigInteger, nullable=False)
    deposit_amount = Column(BigInteger, nullable=False)
    deposit_paid = Column(Boolean, default=False, nullable=False)
    deposit_returned = Column(Boolean, default=False, nullable=False)
    payment_due_day = Column(Integer, default=5)
    status = Column(Enum(ContractStatus), default=ContractStatus.ACTIVE, nullable=False)
    terms = Column(Text)
    pdf_url = Column(String(500))
    signed_at = Column(DateTime(timezone=True))
    terminated_at = Column(DateTime(timezone=True))
    actual_end_date = Column(Date)
    cancel_reason = Column(String(500))
    termination_note = Column(Text)
    member_ids = Column(JSON, default=list)
    vehicle_count = Column(Integer, default=0)

    organization = relationship("Organization")
    room = relationship("Room", back_populates="contracts")
    tenant = relationship("Tenant", back_populates="contracts")
    deposit_transactions = relationship("DepositTransaction", back_populates="contract", cascade="all, delete-orphan")
    contract_logs = relationship("ContractLog", back_populates="contract", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_contracts_room_status", "room_id", "status", "is_archived"),
        Index("ix_contracts_tenant_status", "tenant_id", "status", "is_archived"),
        Index("ix_contracts_org_status", "organization_id", "status", "is_archived"),
        CheckConstraint("end_date > start_date", name="valid_contract_dates"),
        CheckConstraint("monthly_rent >= 0", name="positive_rent"),
        CheckConstraint("deposit_amount >= 0", name="positive_deposit"),
        CheckConstraint("payment_due_day >= 1 AND payment_due_day <= 31", name="valid_due_day"),
        CheckConstraint("vehicle_count >= 0", name="positive_vehicle_count"),
    )


class MeterReading(Base, SoftDeleteMixin):
    __tablename__ = "meter_readings"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    room_id = Column(UUID(as_uuid=False), ForeignKey("rooms.id"), nullable=False, index=True)
    contract_id = Column(UUID(as_uuid=False), ForeignKey("contracts.id"), index=True)
    reading_type = Column(Enum(ReadingType), default=ReadingType.MONTHLY, nullable=False)
    period_start = Column(Date)
    period_end = Column(Date)
    reading_month = Column(Integer, nullable=False)
    reading_year = Column(Integer, nullable=False)
    electricity_previous = Column(Float, default=0)
    electricity_current = Column(Float, nullable=False)
    electricity_usage = Column(Float)
    water_previous = Column(Float, default=0)
    water_current = Column(Float, nullable=False)
    water_usage = Column(Float)
    electricity_image = Column(String(500))
    water_image = Column(String(500))
    is_locked = Column(Boolean, default=False, nullable=False)
    recorded_by = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)

    organization = relationship("Organization")
    room = relationship("Room", back_populates="meter_readings")
    contract = relationship("Contract")

    __table_args__ = (
        Index("ix_meter_readings_room_period", "room_id", "reading_year", "reading_month", "is_archived"),
        Index("ix_meter_readings_contract", "contract_id", "is_archived"),
        CheckConstraint("reading_month >= 1 AND reading_month <= 12", name="valid_month"),
        CheckConstraint("reading_year >= 2020 AND reading_year <= 2100", name="valid_year"),
        CheckConstraint("electricity_current >= electricity_previous", name="valid_electricity_reading"),
        CheckConstraint("water_current >= water_previous", name="valid_water_reading"),
    )


class Invoice(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    room_id = Column(UUID(as_uuid=False), ForeignKey("rooms.id"), nullable=False, index=True)
    contract_id = Column(UUID(as_uuid=False), ForeignKey("contracts.id"), index=True)
    invoice_number = Column(String(50), nullable=False, unique=True, index=True)
    billing_month = Column(Integer, nullable=False)
    billing_year = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)
    rent_amount = Column(BigInteger, nullable=False)
    electricity_amount = Column(BigInteger, default=0)
    water_amount = Column(BigInteger, default=0)
    internet_amount = Column(BigInteger, default=0)
    parking_amount = Column(BigInteger, default=0)
    vehicle_count = Column(Integer, default=0)
    other_amount = Column(BigInteger, default=0)
    discount_amount = Column(BigInteger, default=0)
    old_debt = Column(BigInteger, default=0)
    total_amount = Column(BigInteger, nullable=False)
    paid_amount = Column(BigInteger, default=0)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False)
    qr_code_url = Column(String(500))
    pdf_url = Column(String(500))
    notes = Column(Text)
    paid_at = Column(DateTime(timezone=True))

    organization = relationship("Organization")
    room = relationship("Room", back_populates="invoices")
    contract = relationship("Contract")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_invoices_room_period", "room_id", "billing_year", "billing_month", "is_archived"),
        Index("ix_invoices_org_status", "organization_id", "status", "is_archived"),
        Index("ix_invoices_status_due", "status", "due_date"),
        CheckConstraint("billing_month >= 1 AND billing_month <= 12", name="valid_billing_month"),
        CheckConstraint("billing_year >= 2020 AND billing_year <= 2100", name="valid_billing_year"),
        CheckConstraint("rent_amount >= 0", name="positive_rent_amount"),
        CheckConstraint("total_amount >= 0", name="positive_total_amount"),
        CheckConstraint("paid_amount >= 0", name="positive_paid_amount"),
        CheckConstraint("paid_amount <= total_amount", name="paid_not_exceed_total"),
        CheckConstraint("discount_amount >= 0", name="positive_discount"),
        CheckConstraint("vehicle_count >= 0", name="positive_vehicle_count_invoice"),
    )


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=False), ForeignKey("invoices.id"), nullable=False, index=True)
    description = Column(String(255), nullable=False)
    quantity = Column(Float, default=1)
    unit_price = Column(BigInteger, nullable=False)
    amount = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    invoice = relationship("Invoice", back_populates="items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="positive_quantity"),
        CheckConstraint("amount >= 0", name="positive_item_amount"),
    )


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=False), ForeignKey("invoices.id"), nullable=False, index=True)
    amount = Column(BigInteger, nullable=False)
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.CASH, nullable=False)
    reference_number = Column(String(100))
    notes = Column(Text)
    paid_at = Column(DateTime(timezone=True), server_default=func.now())
    recorded_by = Column(UUID(as_uuid=False), ForeignKey("users.id"))

    invoice = relationship("Invoice", back_populates="payments")

    __table_args__ = (
        Index("ix_payments_invoice", "invoice_id"),
        Index("ix_payments_org_date", "organization_id", "paid_at"),
        CheckConstraint("amount > 0", name="positive_payment_amount"),
    )


class DepositTransaction(Base):
    __tablename__ = "deposit_transactions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    contract_id = Column(UUID(as_uuid=False), ForeignKey("contracts.id"), nullable=False, index=True)
    amount = Column(BigInteger, nullable=False)
    type = Column(Enum(DepositAction), nullable=False)
    reason = Column(String(500))
    performed_by = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    contract = relationship("Contract", back_populates="deposit_transactions")

    __table_args__ = (
        CheckConstraint("amount > 0", name="positive_deposit_amount"),
    )


class ContractLog(Base):
    __tablename__ = "contract_logs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    contract_id = Column(UUID(as_uuid=False), ForeignKey("contracts.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    old_status = Column(String(50))
    new_status = Column(String(50))
    old_data = Column(JSON)
    new_data = Column(JSON)
    performed_by = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    contract = relationship("Contract", back_populates="contract_logs")

    __table_args__ = (
        Index("ix_contract_logs_contract_time", "contract_id", "timestamp"),
    )


class MaintenanceRequest(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "maintenance_requests"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    room_id = Column(UUID(as_uuid=False), ForeignKey("rooms.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id"))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), default="medium")
    status = Column(Enum(MaintenanceStatus), default=MaintenanceStatus.PENDING, nullable=False)
    images = Column(JSON, default=list)
    assigned_to = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)

    organization = relationship("Organization")
    room = relationship("Room", back_populates="maintenance_requests")

    __table_args__ = (
        Index("ix_maintenance_room_status", "room_id", "status", "is_archived"),
        Index("ix_maintenance_org_status", "organization_id", "status", "is_archived"),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    type = Column(Enum(NotificationType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, default=dict)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization")

    __table_args__ = (
        Index("ix_notifications_user_unread", "user_id", "is_read", "created_at"),
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    plan = Column(Enum(SubscriptionPlan), nullable=False)
    price = Column(BigInteger, default=0)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, nullable=False)
    stripe_subscription_id = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="subscriptions")

    __table_args__ = (
        Index("ix_subscriptions_org_active", "organization_id", "is_active"),
        CheckConstraint("price >= 0", name="positive_subscription_price"),
    )


class FeatureEntitlement(Base):
    __tablename__ = "feature_entitlements"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    feature_key = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    source_payment_id = Column(UUID(as_uuid=False), ForeignKey("saas_payments.id"))
    starts_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="feature_entitlements")

    __table_args__ = (
        Index("ix_feature_entitlements_org_key", "organization_id", "feature_key", "is_active"),
    )


class SaaSPayment(Base, TimestampMixin):
    __tablename__ = "saas_payments"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    payment_type = Column(Enum(SaaSPaymentType), nullable=False)
    status = Column(Enum(SaaSPaymentStatus), default=SaaSPaymentStatus.PENDING, nullable=False)
    plan = Column(Enum(SubscriptionPlan))
    feature_key = Column(String(100))
    amount = Column(BigInteger, nullable=False)
    provider = Column(String(50), default="manual")
    checkout_url = Column(String(500))
    reference_number = Column(String(100), unique=True, nullable=False, index=True)
    metadata_json = Column(JSON, default=dict)
    paid_at = Column(DateTime(timezone=True))
    approved_by = Column(UUID(as_uuid=False), ForeignKey("users.id"))

    organization = relationship("Organization", back_populates="saas_payments")
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("ix_saas_payments_org_status", "organization_id", "status"),
        CheckConstraint("amount > 0", name="positive_saas_payment_amount"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), index=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100))
    old_values = Column(JSON)
    new_values = Column(JSON)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_audit_logs_created_at", "created_at"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_org_time", "organization_id", "created_at"),
    )


# --- Tenant Portal Models ---

class TenantOTP(Base):
    __tablename__ = "tenant_otps"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String(255), index=True, nullable=True)
    phone = Column(String(20), index=True, nullable=True)
    otp_code = Column(String(6), nullable=False)
    expired_at = Column(DateTime(timezone=True), nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_tenant_otps_email_verified", "email", "verified", "expired_at"),
        Index("ix_tenant_otps_phone_verified", "phone", "verified", "expired_at"),
    )


class PaymentProof(Base):
    __tablename__ = "payment_proofs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=False), ForeignKey("invoices.id"), nullable=False, index=True)
    image_url = Column(String(500), nullable=False)
    note = Column(Text, nullable=True)
    status = Column(Enum(ProofStatus), default=ProofStatus.PENDING, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    verified_by = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization")
    invoice = relationship("Invoice")

    __table_args__ = (
        Index("ix_payment_proofs_org_status", "organization_id", "status"),
        Index("ix_payment_proofs_invoice", "invoice_id", "status"),
    )


class RepairRequest(Base):
    __tablename__ = "repair_requests"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    contract_id = Column(UUID(as_uuid=False), ForeignKey("contracts.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(RepairStatus), default=RepairStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization")
    contract = relationship("Contract")

    __table_args__ = (
        Index("ix_repair_requests_org_status", "organization_id", "status"),
    )


class RepairRequestImage(Base):
    __tablename__ = "repair_request_images"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    repair_request_id = Column(UUID(as_uuid=False), ForeignKey("repair_requests.id"), nullable=False, index=True)
    image_url = Column(String(500), nullable=False)

    repair_request = relationship("RepairRequest")


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    contract_id = Column(UUID(as_uuid=False), ForeignKey("contracts.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization")
    contract = relationship("Contract")

    __table_args__ = (
        Index("ix_complaints_org_status", "organization_id", "status"),
    )

