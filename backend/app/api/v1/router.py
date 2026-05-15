"""API Router - v1"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    admin,
    auth,
    billing,
    boarding_houses,
    contracts,
    dashboard,
    invoices,
    meter_readings,
    organizations,
    rooms,
    tenants,
    maintenance,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(boarding_houses.router, prefix="/boarding-houses", tags=["Boarding Houses"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["Rooms"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(contracts.router, prefix="/contracts", tags=["Contracts"])
api_router.include_router(meter_readings.router, prefix="/meter-readings", tags=["Meter Readings"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(billing.router, prefix="/billing", tags=["SaaS Billing"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["Maintenance"])
api_router.include_router(admin.router, prefix="/admin", tags=["Platform Admin"])
