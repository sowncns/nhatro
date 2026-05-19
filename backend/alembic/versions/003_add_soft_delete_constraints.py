"""Add soft delete and constraints to all tables

Revision ID: 003_add_soft_delete_constraints
Revises: 002_add_missing_indexes
Create Date: 2026-05-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_soft_delete_constraints'
down_revision = '002_add_missing_indexes'
branch_labels = None
depends_on = None


def upgrade():
    """Add soft delete columns and database constraints"""

    # Add soft delete columns to tables that don't have them
    tables_needing_soft_delete = [
        'boarding_houses', 'rooms', 'tenants', 'room_tenants',
        'contracts', 'meter_readings', 'invoices', 'maintenance_requests'
    ]

    for table in tables_needing_soft_delete:
        # Check if columns exist before adding
        op.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                              WHERE table_name='{table}' AND column_name='is_archived') THEN
                    ALTER TABLE {table} ADD COLUMN is_archived BOOLEAN DEFAULT FALSE NOT NULL;
                END IF;
            END $$;
        """)

        op.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                              WHERE table_name='{table}' AND column_name='archived_at') THEN
                    ALTER TABLE {table} ADD COLUMN archived_at TIMESTAMP WITH TIME ZONE;
                END IF;
            END $$;
        """)

    # Add indexes for soft delete columns
    for table in tables_needing_soft_delete:
        op.execute(f"""
            CREATE INDEX IF NOT EXISTS ix_{table}_is_archived
            ON {table} (is_archived);
        """)

        op.execute(f"""
            CREATE INDEX IF NOT EXISTS ix_{table}_archived_at
            ON {table} (archived_at) WHERE archived_at IS NOT NULL;
        """)

    # Add check constraints for data validation

    # Users table
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_email') THEN
                ALTER TABLE users ADD CONSTRAINT valid_email
                CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$');
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_full_name') THEN
                ALTER TABLE users ADD CONSTRAINT valid_full_name
                CHECK (length(full_name) >= 2);
            END IF;
        END $$;
    """)

    # Organizations table
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_org_name') THEN
                ALTER TABLE organizations ADD CONSTRAINT valid_org_name
                CHECK (length(name) >= 2);
            END IF;
        END $$;
    """)

    # Rooms table
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'positive_base_price') THEN
                ALTER TABLE rooms ADD CONSTRAINT positive_base_price
                CHECK (base_price >= 0);
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'positive_electricity_price') THEN
                ALTER TABLE rooms ADD CONSTRAINT positive_electricity_price
                CHECK (electricity_price >= 0);
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'positive_water_price') THEN
                ALTER TABLE rooms ADD CONSTRAINT positive_water_price
                CHECK (water_price >= 0);
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'positive_max_occupants') THEN
                ALTER TABLE rooms ADD CONSTRAINT positive_max_occupants
                CHECK (max_occupants > 0);
            END IF;
        END $$;
    """)

    # Contracts table
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_contract_dates') THEN
                ALTER TABLE contracts ADD CONSTRAINT valid_contract_dates
                CHECK (end_date > start_date);
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'positive_rent') THEN
                ALTER TABLE contracts ADD CONSTRAINT positive_rent
                CHECK (monthly_rent >= 0);
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'positive_deposit') THEN
                ALTER TABLE contracts ADD CONSTRAINT positive_deposit
                CHECK (deposit_amount >= 0);
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_due_day') THEN
                ALTER TABLE contracts ADD CONSTRAINT valid_due_day
                CHECK (payment_due_day >= 1 AND payment_due_day <= 31);
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'positive_vehicle_count') THEN
                ALTER TABLE contracts ADD CONSTRAINT positive_vehicle_count
                CHECK (vehicle_count >= 0);
            END IF;
        END $$;
    """)

    # Invoices table
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_billing_month') THEN
                ALTER TABLE invoices ADD CONSTRAINT valid_billing_month
                CHECK (billing_month >= 1 AND billing_month <= 12);
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'positive_total_amount') THEN
                ALTER TABLE invoices ADD CONSTRAINT positive_total_amount
                CHECK (total_amount >= 0);
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'positive_paid_amount') THEN
                ALTER TABLE invoices ADD CONSTRAINT positive_paid_amount
                CHECK (paid_amount >= 0);
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'paid_not_exceed_total') THEN
                ALTER TABLE invoices ADD CONSTRAINT paid_not_exceed_total
                CHECK (paid_amount <= total_amount);
            END IF;
        END $$;
    """)

    # Payments table
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'positive_payment_amount') THEN
                ALTER TABLE payments ADD CONSTRAINT positive_payment_amount
                CHECK (amount > 0);
            END IF;
        END $$;
    """)

    # Meter readings table
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_month') THEN
                ALTER TABLE meter_readings ADD CONSTRAINT valid_month
                CHECK (reading_month >= 1 AND reading_month <= 12);
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_year') THEN
                ALTER TABLE meter_readings ADD CONSTRAINT valid_year
                CHECK (reading_year >= 2020 AND reading_year <= 2100);
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_electricity_reading') THEN
                ALTER TABLE meter_readings ADD CONSTRAINT valid_electricity_reading
                CHECK (electricity_current >= electricity_previous);
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_water_reading') THEN
                ALTER TABLE meter_readings ADD CONSTRAINT valid_water_reading
                CHECK (water_current >= water_previous);
            END IF;
        END $$;
    """)

    # Add composite indexes for better query performance
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_contracts_org_status_archived
        ON contracts (organization_id, status, is_archived);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_invoices_org_status_archived
        ON invoices (organization_id, status, is_archived);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_rooms_org_status_archived
        ON rooms (organization_id, status, is_archived);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_invoices_status_due
        ON invoices (status, due_date) WHERE is_archived = FALSE;
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_contracts_room_status_archived
        ON contracts (room_id, status, is_archived);
    """)


def downgrade():
    """Remove soft delete columns and constraints"""

    # Drop check constraints
    constraints = [
        ('users', 'valid_email'),
        ('users', 'valid_full_name'),
        ('organizations', 'valid_org_name'),
        ('rooms', 'positive_base_price'),
        ('rooms', 'positive_electricity_price'),
        ('rooms', 'positive_water_price'),
        ('rooms', 'positive_max_occupants'),
        ('contracts', 'valid_contract_dates'),
        ('contracts', 'positive_rent'),
        ('contracts', 'positive_deposit'),
        ('contracts', 'valid_due_day'),
        ('contracts', 'positive_vehicle_count'),
        ('invoices', 'valid_billing_month'),
        ('invoices', 'positive_total_amount'),
        ('invoices', 'positive_paid_amount'),
        ('invoices', 'paid_not_exceed_total'),
        ('payments', 'positive_payment_amount'),
        ('meter_readings', 'valid_month'),
        ('meter_readings', 'valid_year'),
        ('meter_readings', 'valid_electricity_reading'),
        ('meter_readings', 'valid_water_reading'),
    ]

    for table, constraint in constraints:
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint};")

    # Drop indexes
    indexes = [
        'ix_contracts_org_status_archived',
        'ix_invoices_org_status_archived',
        'ix_rooms_org_status_archived',
        'ix_invoices_status_due',
        'ix_contracts_room_status_archived',
    ]

    for index in indexes:
        op.execute(f"DROP INDEX IF EXISTS {index};")

    # Drop soft delete columns
    tables = [
        'boarding_houses', 'rooms', 'tenants', 'room_tenants',
        'contracts', 'meter_readings', 'invoices', 'maintenance_requests'
    ]

    for table in tables:
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS is_archived;")
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS archived_at;")
