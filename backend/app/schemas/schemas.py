"""Pydantic schemas for API request/response validation"""
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List, Any, Dict
from datetime import date, datetime
from enum import Enum


# ─────────────────────────────────────────────
# AUTH SCHEMAS
# ─────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    organization_name: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginPolicy(str, Enum):
    REJECT_NEW_LOGIN = "reject_new_login"
    REVOKE_OLDEST_SESSION = "revoke_oldest_session"
    REVOKE_ALL_OLD_SESSIONS = "revoke_all_old_sessions"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_id: str
    device_name: Optional[str] = None
    policy: Optional[LoginPolicy] = LoginPolicy.REVOKE_OLDEST_SESSION


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class TenantOTPSendRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class TenantOTPVerifyRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    otp_code: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


# ─────────────────────────────────────────────
# USER / ORG SCHEMAS
# ─────────────────────────────────────────────

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    full_name: str
    phone: Optional[str]
    avatar_url: Optional[str]
    role: str
    is_active: bool
    created_at: datetime


class UserSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    device_id: str
    device_name: Optional[str]
    user_agent: Optional[str]
    ip_address: Optional[str]
    last_seen: datetime
    is_active: bool
    created_at: datetime


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    slug: str
    subscription_plan: str
    logo_url: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    bank_name: Optional[str]
    bank_account: Optional[str]
    bank_account_name: Optional[str]
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_account_name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────────────
# BOARDING HOUSE SCHEMAS
# ─────────────────────────────────────────────

class BoardingHouseCreate(BaseModel):
    name: str
    address: str
    description: Optional[str] = None
    total_floors: int = 1


class BoardingHouseUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    total_floors: Optional[int] = None


class BoardingHouseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    address: str
    description: Optional[str]
    images: List[str]
    total_floors: int
    is_active: bool
    created_at: datetime


# ─────────────────────────────────────────────
# ROOM SCHEMAS
# ─────────────────────────────────────────────

class RoomCreate(BaseModel):
    boarding_house_id: str
    room_number: str
    floor: int = 1
    area: Optional[float] = None
    max_occupants: int = 2
    base_price: int
    electricity_price: Optional[int] = None
    water_price: Optional[int] = None
    internet_fee: Optional[int] = None
    parking_fee: Optional[int] = None
    amenities: List[str] = []
    notes: Optional[str] = None


class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    floor: Optional[int] = None
    area: Optional[float] = None
    base_price: Optional[int] = None
    electricity_price: Optional[int] = None
    water_price: Optional[int] = None
    internet_fee: Optional[int] = None
    parking_fee: Optional[int] = None
    status: Optional[str] = None
    amenities: Optional[List[str]] = None
    notes: Optional[str] = None


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    boarding_house_id: str
    room_number: str
    floor: int
    area: Optional[float]
    max_occupants: int
    base_price: int
    electricity_price: int
    water_price: int
    internet_fee: int
    parking_fee: int
    status: str
    amenities: List[str]
    images: List[str]
    notes: Optional[str]
    created_at: datetime


# ─────────────────────────────────────────────
# TENANT SCHEMAS
# ─────────────────────────────────────────────

class TenantCreate(BaseModel):
    full_name: str
    phone: str
    email: Optional[str] = None
    id_card: str
    date_of_birth: Optional[date] = None
    permanent_address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    notes: Optional[str] = None


class TenantUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    id_card: Optional[str] = None
    date_of_birth: Optional[date] = None
    permanent_address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    notes: Optional[str] = None


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    full_name: str
    phone: str
    email: Optional[str]
    id_card: Optional[str]
    date_of_birth: Optional[date]
    permanent_address: Optional[str]
    avatar_url: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    is_active: bool
    created_at: datetime


# ─────────────────────────────────────────────
# CONTRACT SCHEMAS
# ─────────────────────────────────────────────

class ContractCreate(BaseModel):
    room_id: str
    tenant_id: str
    start_date: date
    end_date: date
    monthly_rent: int
    deposit_amount: int
    payment_due_day: int = 5
    terms: Optional[str] = None
    member_ids: List[str] = Field(default_factory=list)
    vehicle_count: int = 0


class ContractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    room_id: str
    tenant_id: str
    contract_number: str
    start_date: date
    end_date: date
    monthly_rent: int = 0
    deposit_amount: int = 0
    deposit_paid: bool = False
    deposit_returned: bool = False
    payment_due_day: int = 5
    status: str
    member_ids: List[str] = []
    vehicle_count: int = 0
    pdf_url: Optional[str] = None
    actual_end_date: Optional[date] = None
    cancel_reason: Optional[str] = None
    termination_note: Optional[str] = None
    created_at: datetime


class DepositDeduction(BaseModel):
    amount: int
    reason: str


class ContractTerminateRequest(BaseModel):
    actual_end_date: date
    termination_note: Optional[str] = None
    final_electricity: float
    final_water: float
    deposit_deductions: List[DepositDeduction] = Field(default_factory=list)
    refund_amount: int = 0
    move_out_reason: Optional[str] = None


class DepositTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    amount: int
    type: str
    reason: Optional[str]
    created_at: datetime


class ContractLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    action: str
    old_status: Optional[str]
    new_status: Optional[str]
    timestamp: datetime


# ─────────────────────────────────────────────
# METER READING SCHEMAS
# ─────────────────────────────────────────────

class MeterReadingCreate(BaseModel):
    room_id: str
    contract_id: Optional[str] = None
    reading_type: str = "MONTHLY"
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    reading_month: int
    reading_year: int
    electricity_previous: Optional[float] = None
    electricity_current: float
    water_previous: Optional[float] = None
    water_current: float
    notes: Optional[str] = None


class MeterReadingUpdate(BaseModel):
    electricity_previous: Optional[float] = None
    electricity_current: Optional[float] = None
    water_previous: Optional[float] = None
    water_current: Optional[float] = None
    notes: Optional[str] = None


class MeterReadingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    room_id: str
    contract_id: Optional[str]
    reading_type: str
    period_start: Optional[date]
    period_end: Optional[date]
    reading_month: int
    reading_year: int
    electricity_previous: float
    electricity_current: float
    electricity_usage: Optional[float]
    water_previous: float
    water_current: float
    water_usage: Optional[float]
    is_locked: bool
    electricity_image: Optional[str]
    water_image: Optional[str]
    notes: Optional[str]
    recorded_at: datetime


# ─────────────────────────────────────────────
# INVOICE SCHEMAS
# ─────────────────────────────────────────────

class InvoiceCreate(BaseModel):
    room_id: str
    billing_month: int
    billing_year: int
    rent_amount: int
    electricity_amount: int = 0
    water_amount: int = 0
    internet_amount: int = 0
    parking_amount: int = 0
    vehicle_count: int = 0
    other_amount: int = 0
    discount_amount: int = 0
    old_debt: int = 0
    due_date: date
    notes: Optional[str] = None


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    room_id: str
    invoice_number: str
    billing_month: int
    billing_year: int
    due_date: date
    rent_amount: int
    electricity_amount: int
    water_amount: int
    internet_amount: int
    parking_amount: int
    vehicle_count: int
    other_amount: int
    discount_amount: int
    old_debt: int
    total_amount: int
    paid_amount: int
    status: str
    representative_name: Optional[str] = None
    qr_code_url: Optional[str]
    pdf_url: Optional[str]
    notes: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime


# ─────────────────────────────────────────────
# DASHBOARD SCHEMAS
# ─────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_rooms: int
    occupied_rooms: int
    available_rooms: int
    occupancy_rate: float
    total_tenants: int
    total_revenue_month: int
    total_outstanding: int
    expiring_contracts: int
    pending_maintenance: int


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int


# ─────────────────────────────────────────────
# SAAS BILLING / ADMIN SCHEMAS
# ─────────────────────────────────────────────

class PlanInfo(BaseModel):
    key: str
    name: str
    price: int
    max_rooms: Optional[int] = None
    features: List[str]
    is_current: bool = False


class FeatureModuleInfo(BaseModel):
    key: str
    name: str
    description: str
    price: int
    is_enabled: bool = False


class CheckoutRequest(BaseModel):
    plan: Optional[str] = None
    feature_key: Optional[str] = None
    provider: str = "manual"


class CheckoutResponse(BaseModel):
    payment_id: str
    reference_number: str
    amount: int
    status: str
    checkout_url: str


class SaaSPaymentResponse(BaseModel):
    id: str
    organization_id: str
    user_id: str
    payment_type: str
    status: str
    plan: Optional[str] = None
    feature_key: Optional[str] = None
    amount: int
    provider: str
    reference_number: str
    checkout_url: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime


class BillingOverview(BaseModel):
    organization_id: str
    organization_name: str
    current_plan: str
    plans: List[PlanInfo]
    modules: List[FeatureModuleInfo]
    recent_payments: List[SaaSPaymentResponse]


class PlatformCustomerResponse(BaseModel):
    organization_id: str
    organization_name: str
    owner_email: str
    owner_name: str
    plan: str
    is_active: bool
    created_at: datetime


class PlatformStatsResponse(BaseModel):
    owners: int
    organizations: int
    active_subscriptions: int
    paid_revenue: int
    pending_payments: int

# ─────────────────────────────────────────────
# MAINTENANCE SCHEMAS
# ─────────────────────────────────────────────

class MaintenanceCreate(BaseModel):
    room_id: str
    tenant_id: Optional[str] = None
    title: str
    description: str
    priority: str = "medium"

class MaintenanceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None

class MaintenanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    room_id: str
    tenant_id: Optional[str]
    title: str
    description: str
    priority: str
    status: str
    images: List[str]
    assigned_to: Optional[str]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    created_at: datetime


# ─────────────────────────────────────────────
# TERMINATION SCHEMAS
# ─────────────────────────────────────────────

class DepositDeduction(BaseModel):
    reason: str
    amount: int

class ContractTerminateRequest(BaseModel):
    actual_end_date: date
    final_electricity: float
    final_water: float
    refund_amount: int
    move_out_reason: Optional[str] = "Kết thúc hợp đồng"
    termination_note: Optional[str] = None
    deposit_deductions: List[DepositDeduction] = []


class ComplaintCreate(BaseModel):
    title: str
    description: str
    contract_id: str


class RepairRequestCreate(BaseModel):
    title: str
    description: str
    contract_id: str
