"""Add missing database indexes

Revision ID: 002_add_missing_indexes
Revises: 001_initial
Create Date: 2026-05-15

Adds composite and single-column indexes for the most common query patterns:
- rooms: boarding_house_id (list rooms by house)
- contracts: room_id, tenant_id, (room_id + status) composite
- meter_readings: room_id, (room_id + year + month) composite
- invoices: room_id, status, (room_id + year + month), (org_id + status)
- invoice_items: invoice_id
- payments: invoice_id
- notifications: user_id, (user_id + is_read) composite
- room_tenants: room_id, tenant_id
- maintenance_requests: room_id, status
- audit_logs: created_at, resource_type
- subscriptions: organization_id, (org_id + is_active) composite
"""
from alembic import op

revision = '002_add_missing_indexes'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── rooms ──────────────────────────────────────────────────────────────
    op.create_index('ix_rooms_boarding_house_id', 'rooms', ['boarding_house_id'])

    # ── room_tenants ───────────────────────────────────────────────────────
    op.create_index('ix_room_tenants_room_id', 'room_tenants', ['room_id'])
    op.create_index('ix_room_tenants_tenant_id', 'room_tenants', ['tenant_id'])

    # ── contracts ──────────────────────────────────────────────────────────
    op.create_index('ix_contracts_room_id', 'contracts', ['room_id'])
    op.create_index('ix_contracts_tenant_id', 'contracts', ['tenant_id'])
    op.create_index('ix_contracts_room_status', 'contracts', ['room_id', 'status'])

    # ── meter_readings ─────────────────────────────────────────────────────
    op.create_index('ix_meter_readings_room_id', 'meter_readings', ['room_id'])
    op.create_index(
        'ix_meter_readings_room_period',
        'meter_readings',
        ['room_id', 'reading_year', 'reading_month'],
    )

    # ── invoices ───────────────────────────────────────────────────────────
    op.create_index('ix_invoices_room_id', 'invoices', ['room_id'])
    op.create_index('ix_invoices_status', 'invoices', ['status'])
    op.create_index(
        'ix_invoices_room_period',
        'invoices',
        ['room_id', 'billing_year', 'billing_month'],
    )
    op.create_index(
        'ix_invoices_org_status',
        'invoices',
        ['organization_id', 'status'],
    )

    # ── invoice_items ──────────────────────────────────────────────────────
    op.create_index('ix_invoice_items_invoice_id', 'invoice_items', ['invoice_id'])

    # ── payments ───────────────────────────────────────────────────────────
    op.create_index('ix_payments_invoice_id', 'payments', ['invoice_id'])

    # ── notifications ──────────────────────────────────────────────────────
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index(
        'ix_notifications_user_unread',
        'notifications',
        ['user_id', 'is_read'],
    )

    # ── maintenance_requests ───────────────────────────────────────────────
    op.create_index('ix_maintenance_requests_room_id', 'maintenance_requests', ['room_id'])
    op.create_index('ix_maintenance_requests_status', 'maintenance_requests', ['status'])

    # ── audit_logs ─────────────────────────────────────────────────────────
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])

    # ── subscriptions ──────────────────────────────────────────────────────
    op.create_index('ix_subscriptions_organization_id', 'subscriptions', ['organization_id'])
    op.create_index(
        'ix_subscriptions_org_active',
        'subscriptions',
        ['organization_id', 'is_active'],
    )


def downgrade() -> None:
    op.drop_index('ix_subscriptions_org_active', table_name='subscriptions')
    op.drop_index('ix_subscriptions_organization_id', table_name='subscriptions')
    op.drop_index('ix_audit_logs_resource_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('ix_maintenance_requests_status', table_name='maintenance_requests')
    op.drop_index('ix_maintenance_requests_room_id', table_name='maintenance_requests')
    op.drop_index('ix_notifications_user_unread', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_index('ix_payments_invoice_id', table_name='payments')
    op.drop_index('ix_invoice_items_invoice_id', table_name='invoice_items')
    op.drop_index('ix_invoices_org_status', table_name='invoices')
    op.drop_index('ix_invoices_room_period', table_name='invoices')
    op.drop_index('ix_invoices_status', table_name='invoices')
    op.drop_index('ix_invoices_room_id', table_name='invoices')
    op.drop_index('ix_meter_readings_room_period', table_name='meter_readings')
    op.drop_index('ix_meter_readings_room_id', table_name='meter_readings')
    op.drop_index('ix_contracts_room_status', table_name='contracts')
    op.drop_index('ix_contracts_tenant_id', table_name='contracts')
    op.drop_index('ix_contracts_room_id', table_name='contracts')
    op.drop_index('ix_room_tenants_tenant_id', table_name='room_tenants')
    op.drop_index('ix_room_tenants_room_id', table_name='room_tenants')
    op.drop_index('ix_rooms_boarding_house_id', table_name='rooms')
