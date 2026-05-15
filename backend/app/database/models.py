"""
SQLAlchemy ORM Models - Multi-tenant SaaS NhaTro
ALL business tables include organization_id for tenant isolation
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, Enum, JSON, Date, BigInteger, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func
import enum


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

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20))
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(Enum(UserRole), default=UserRole.OWNER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    organizations = relationship("Organization", back_populates="owner")
    org_memberships = relationship("OrganizationMember", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    owner_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    subscription_plan = Column(Enum(SubscriptionPlan), default=SubscriptionPlan.FREE)
    logo_url = Column(String(500))
    address = Column(String(500))
    phone = Column(String(20))
    bank_name = Column(String(100))
    bank_account = Column(String(50))
    bank_account_name = Column(String(100))
    settings = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    owner = relationship("User", back_populates="organizations")
    members = relationship("OrganizationMember", back_populates="organization")
    boarding_houses = relationship("BoardingHouse", back_populates="organization")
    subscriptions = relationship("Subscription", back_populates="organization")
    feature_entitlements = relationship("FeatureEntitlement", back_populates="organization")
    saas_payments = relationship("SaaSPayment", back_populates="organization")


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    role = Column(Enum(OrgMemberRole), default=OrgMemberRole.STAFF)
    permissions = Column(JSON, default=list)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="org_memberships")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    token = Column(String(500), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="refresh_tokens")


# ─────────────────────────────────────────────
# BUSINESS TABLES (all have organization_id)
# ─────────────────────────────────────────────

class BoardingHouse(Base):
    __tablename__ = "boarding_houses"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=False)
    description = Column(Text)
    images = Column(JSON, default=list)
    total_floors = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization", back_populates="boarding_houses")
    rooms = relationship("Room", back_populates="boarding_house")


class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = (
        Index("ix_rooms_boarding_house_id", "boarding_house_id"),
    )

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    boarding_house_id = Column(UUID(as_uuid=False), ForeignKey("boarding_houses.id"), nullable=False)
    room_number = Column(String(20), nullable=False)
    floor = Column(Integer, default=1)
    area = Column(Float)  # m2
    max_occupants = Column(Integer, default=2)
    base_price = Column(BigInteger, nullable=False)  # VND
    electricity_price = Column(BigInteger, default=4000)  # per kWh
    water_price = Column(BigInteger, default=15000)  # per m3
    internet_fee = Column(BigInteger, default=0)
    parking_fee = Column(BigInteger, default=0)
    status = Column(Enum(RoomStatus), default=RoomStatus.AVAILABLE)
    amenities = Column(JSON, default=list)
    images = Column(JSON, default=list)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization")
    boarding_house = relationship("BoardingHouse", back_populates="rooms")
    tenants = relationship("RoomTenant", back_populates="room")
    contracts = relationship("Contract", back_populates="room")
    meter_readings = relationship("MeterReading", back_populates="room")
    invoices = relationship("Invoice", back_populates="room")
    maintenance_requests = relationship("MaintenanceRequest", back_populates="room")


class Tenant(Base):
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
    is_active = Column(Boolean, default=True)
    archived_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization")
    room_tenants = relationship("RoomTenant", back_populates="tenant")
    contracts = relationship("Contract", back_populates="tenant")


class RoomTenant(Base):
    """Many-to-many: multiple tenants can share a room"""
    __tablename__ = "room_tenants"
    __table_args__ = (
        Index("ix_room_tenants_room_id", "room_id"),
        Index("ix_room_tenants_tenant_id", "tenant_id"),
    )

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    room_id = Column(UUID(as_uuid=False), ForeignKey("rooms.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False)
    is_primary = Column(Boolean, default=False)  # Người thuê chính
    move_in_date = Column(Date, nullable=False)
    move_out_date = Column(Date)
    move_out_reason = Column(String(500))
    is_active = Column(Boolean, default=True)

    room = relationship("Room", back_populates="tenants")
    tenant = relationship("Tenant", back_populates="room_tenants")


class Contract(Base):
    __tablename__ = "contracts"
    __table_args__ = (
        Index("ix_contracts_room_id", "room_id"),
        Index("ix_contracts_tenant_id", "tenant_id"),
        Index("ix_contracts_room_status", "room_id", "status"),
    )

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    room_id = Column(UUID(as_uuid=False), ForeignKey("rooms.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False)
    contract_number = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    monthly_rent = Column(BigInteger, nullable=False)
    deposit_amount = Column(BigInteger, nullable=False)
    deposit_paid = Column(Boolean, default=False)
    deposit_returned = Column(Boolean, default=False)
    payment_due_day = Column(Integer, default=5)  # day of month
    status = Column(Enum(ContractStatus), default=ContractStatus.ACTIVE)
    terms = Column(Text)
    pdf_url = Column(String(500))
    signed_at = Column(DateTime(timezone=True))
    terminated_at = Column(DateTime(timezone=True))
    actual_end_date = Column(Date)
    cancel_reason = Column(String(500))
    termination_note = Column(Text)
    member_ids = Column(JSON, default=list)  # Lưu danh sách ID những người ở cùng (co-tenants)
    vehicle_count = Column(Integer, default=0) # Số lượng xe gửi
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization")
    room = relationship("Room", back_populates="contracts")
    tenant = relationship("Tenant", back_populates="contracts")
    deposit_transactions = relationship("DepositTransaction", back_populates="contract", cascade="all, delete-orphan")
    contract_logs = relationship("ContractLog", back_populates="contract", cascade="all, delete-orphan")
    archived_at = Column(DateTime(timezone=True))


class MeterReading(Base):
    __tablename__ = "meter_readings"
    __table_args__ = (
        Index("ix_meter_readings_room_id", "room_id"),
        Index("ix_meter_readings_room_period", "room_id", "reading_year", "reading_month"),
    )

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    room_id = Column(UUID(as_uuid=False), ForeignKey("rooms.id"), nullable=False)
    contract_id = Column(UUID(as_uuid=False), ForeignKey("contracts.id"), index=True)
    reading_type = Column(Enum(ReadingType), default=ReadingType.MONTHLY)
    period_start = Column(Date)
    period_end = Column(Date)
    reading_month = Column(Integer, nullable=False)  # 1-12
    reading_year = Column(Integer, nullable=False)
    electricity_previous = Column(Float, default=0)
    electricity_current = Column(Float, nullable=False)
    electricity_usage = Column(Float)  # computed
    water_previous = Column(Float, default=0)
    water_current = Column(Float, nullable=False)
    water_usage = Column(Float)  # computed
    electricity_image = Column(String(500))
    water_image = Column(String(500))
    is_locked = Column(Boolean, default=False)
    recorded_by = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)
    archived_at = Column(DateTime(timezone=True))

    organization = relationship("Organization")
    room = relationship("Room", back_populates="meter_readings")
    contract = relationship("Contract")


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_room_id", "room_id"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_room_period", "room_id", "billing_year", "billing_month"),
        Index("ix_invoices_org_status", "organization_id", "status"),
    )

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    room_id = Column(UUID(as_uuid=False), ForeignKey("rooms.id"), nullable=False)
    contract_id = Column(UUID(as_uuid=False), ForeignKey("contracts.id"))
    invoice_number = Column(String(50), nullable=False, unique=True)
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
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    qr_code_url = Column(String(500))
    pdf_url = Column(String(500))
    notes = Column(Text)
    paid_at = Column(DateTime(timezone=True))
    archived_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization")
    room = relationship("Room", back_populates="invoices")
    contract = relationship("Contract")
    items = relationship("InvoiceItem", back_populates="invoice")
    payments = relationship("Payment", back_populates="invoice")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    __table_args__ = (
        Index("ix_invoice_items_invoice_id", "invoice_id"),
    )

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=False), ForeignKey("invoices.id"), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Float, default=1)
    unit_price = Column(BigInteger, nullable=False)
    amount = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    invoice = relationship("Invoice", back_populates="items")


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_invoice_id", "invoice_id"),
    )

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=False), ForeignKey("invoices.id"), nullable=False)
    amount = Column(BigInteger, nullable=False)
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.CASH)
    reference_number = Column(String(100))
    notes = Column(Text)
    paid_at = Column(DateTime(timezone=True), server_default=func.now())
    recorded_by = Column(UUID(as_uuid=False), ForeignKey("users.id"))

    invoice = relationship("Invoice", back_populates="payments")


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


class ContractLog(Base):
    __tablename__ = "contract_logs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    contract_id = Column(UUID(as_uuid=False), ForeignKey("contracts.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False) # e.g., "TERMINATE", "CANCEL", "SETTLE_DEPOSIT"
    old_status = Column(String(50))
    new_status = Column(String(50))
    old_data = Column(JSON)
    new_data = Column(JSON)
    performed_by = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    contract = relationship("Contract", back_populates="contract_logs")


class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"
    __table_args__ = (
        Index("ix_maintenance_requests_room_id", "room_id"),
        Index("ix_maintenance_requests_status", "status"),
    )

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    room_id = Column(UUID(as_uuid=False), ForeignKey("rooms.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id"))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    status = Column(Enum(MaintenanceStatus), default=MaintenanceStatus.PENDING)
    images = Column(JSON, default=list)
    assigned_to = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    archived_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization")
    room = relationship("Room", back_populates="maintenance_requests")


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_user_unread", "user_id", "is_read"),
    )

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    type = Column(Enum(NotificationType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, default=dict)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization")


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("ix_subscriptions_organization_id", "organization_id"),
        Index("ix_subscriptions_org_active", "organization_id", "is_active"),
    )

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    plan = Column(Enum(SubscriptionPlan), nullable=False)
    price = Column(BigInteger, default=0)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    stripe_subscription_id = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="subscriptions")


class FeatureEntitlement(Base):
    __tablename__ = "feature_entitlements"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    feature_key = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    source_payment_id = Column(UUID(as_uuid=False), ForeignKey("saas_payments.id"))
    starts_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="feature_entitlements")


class SaaSPayment(Base):
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization", back_populates="saas_payments")
    user = relationship("User", foreign_keys=[user_id])


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_created_at", "created_at"),
        Index("ix_audit_logs_resource_type", "resource_type"),
    )

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
