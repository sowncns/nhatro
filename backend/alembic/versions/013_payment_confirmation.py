"""Add payment confirmation fields

Revision ID: 013_payment_confirmation
Revises: c6905d5ff883
Create Date: 2026-05-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '013_payment_confirmation'
down_revision = 'c6905d5ff883'
branch_labels = None
depends_on = None


def upgrade():
    """Idempotent migration for payment proof confirmation flow."""

    # Add columns safely (PostgreSQL)
    op.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS contract_id UUID")
    op.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS payment_date TIMESTAMP WITH TIME ZONE")
    op.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'confirmed'")
    op.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS proof_image_url VARCHAR(500)")
    op.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS confirmed_by UUID")
    op.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMP WITH TIME ZONE")
    op.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT now()")

    # Backfill existing records
    op.execute("UPDATE payments SET status = 'confirmed' WHERE status IS NULL")
    op.execute("UPDATE payments SET created_at = COALESCE(paid_at, now()) WHERE created_at IS NULL")

    # Add foreign keys safely
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'fk_payments_contract_id'
        ) THEN
            ALTER TABLE payments
            ADD CONSTRAINT fk_payments_contract_id
            FOREIGN KEY (contract_id) REFERENCES contracts(id);
        END IF;
    END $$;
    """)

    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'fk_payments_confirmed_by'
        ) THEN
            ALTER TABLE payments
            ADD CONSTRAINT fk_payments_confirmed_by
            FOREIGN KEY (confirmed_by) REFERENCES users(id);
        END IF;
    END $$;
    """)

    # Add indexes safely
    op.execute("CREATE INDEX IF NOT EXISTS ix_payments_status ON payments(status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_payments_org_status ON payments(organization_id, status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_payments_contract_id ON payments(contract_id)")

    # Add invoice enum values safely (PostgreSQL enum)
    op.execute("ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'UNPAID'")
    op.execute("ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'PENDING_CONFIRMATION'")


def downgrade():
    """Best-effort downgrade. Enum values cannot be removed safely in PostgreSQL."""
    op.execute("DROP INDEX IF EXISTS ix_payments_contract_id")
    op.execute("DROP INDEX IF EXISTS ix_payments_org_status")
    op.execute("DROP INDEX IF EXISTS ix_payments_status")

    op.execute("ALTER TABLE payments DROP CONSTRAINT IF EXISTS fk_payments_confirmed_by")
    op.execute("ALTER TABLE payments DROP CONSTRAINT IF EXISTS fk_payments_contract_id")

    op.execute("ALTER TABLE payments DROP COLUMN IF EXISTS created_at")
    op.execute("ALTER TABLE payments DROP COLUMN IF EXISTS confirmed_at")
    op.execute("ALTER TABLE payments DROP COLUMN IF EXISTS confirmed_by")
    op.execute("ALTER TABLE payments DROP COLUMN IF EXISTS proof_image_url")
    op.execute("ALTER TABLE payments DROP COLUMN IF EXISTS status")
    op.execute("ALTER TABLE payments DROP COLUMN IF EXISTS payment_date")
    op.execute("ALTER TABLE payments DROP COLUMN IF EXISTS contract_id")
