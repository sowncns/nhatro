"""Add termination history and debt records

Revision ID: 9b3c2a1c4d11
Revises: f0924b97c02a
Create Date: 2026-05-24

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9b3c2a1c4d11"
down_revision = "f0924b97c02a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'terminationtype') THEN
                    CREATE TYPE terminationtype AS ENUM (
                        'TENANT_EARLY_TERMINATION',
                        'ABANDONED_ROOM',
                        'CONTRACT_EXPIRED',
                        'LANDLORD_TERMINATION',
                        'FORCE_MAJEURE'
                    );
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'debtstatus') THEN
                    CREATE TYPE debtstatus AS ENUM ('OPEN', 'SETTLED', 'WRITTEN_OFF');
                END IF;

                BEGIN ALTER TYPE contractstatus ADD VALUE IF NOT EXISTS 'PAYMENT_OVERDUE'; EXCEPTION WHEN duplicate_object THEN NULL; END;
                BEGIN ALTER TYPE contractstatus ADD VALUE IF NOT EXISTS 'NO_RESPONSE'; EXCEPTION WHEN duplicate_object THEN NULL; END;
                BEGIN ALTER TYPE contractstatus ADD VALUE IF NOT EXISTS 'ABANDONED_ROOM'; EXCEPTION WHEN duplicate_object THEN NULL; END;

                BEGIN ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'UNPAID'; EXCEPTION WHEN duplicate_object THEN NULL; END;
                BEGIN ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'PARTIAL'; EXCEPTION WHEN duplicate_object THEN NULL; END;
            END $$;
            """
        )

    op.create_table(
        "termination_histories",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("organization_id", sa.UUID(as_uuid=False), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("contract_id", sa.UUID(as_uuid=False), sa.ForeignKey("contracts.id"), nullable=False),
        sa.Column("termination_type", sa.Enum(name="terminationtype"), nullable=False),
        sa.Column("reason", sa.String(length=500)),
        sa.Column("note", sa.Text()),
        sa.Column("created_by", sa.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("final_invoice_id", sa.UUID(as_uuid=False), sa.ForeignKey("invoices.id")),
        sa.Column("deposit_used", sa.BigInteger(), server_default="0"),
        sa.Column("refund_amount", sa.BigInteger(), server_default="0"),
        sa.Column("remaining_debt", sa.BigInteger(), server_default="0"),
        sa.Column("contract_snapshot", sa.dialects.postgresql.JSONB() if bind.dialect.name == "postgresql" else sa.JSON()),
        sa.Column("metadata", sa.dialects.postgresql.JSONB() if bind.dialect.name == "postgresql" else sa.JSON()),
    )
    op.create_index("ix_termination_histories_contract_id", "termination_histories", ["contract_id"])
    op.create_index("ix_termination_histories_org_created", "termination_histories", ["organization_id", "created_at"])

    op.create_table(
        "debt_records",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("organization_id", sa.UUID(as_uuid=False), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("contract_id", sa.UUID(as_uuid=False), sa.ForeignKey("contracts.id"), nullable=False),
        sa.Column("tenant_id", sa.UUID(as_uuid=False), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("invoice_id", sa.UUID(as_uuid=False), sa.ForeignKey("invoices.id")),
        sa.Column("amount", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("status", sa.Enum(name="debtstatus"), nullable=False, server_default="OPEN"),
        sa.Column("risk_flag", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index("ix_debt_records_contract_id", "debt_records", ["contract_id"])
    op.create_index("ix_debt_records_org_status", "debt_records", ["organization_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_debt_records_org_status", table_name="debt_records")
    op.drop_index("ix_debt_records_contract_id", table_name="debt_records")
    op.drop_table("debt_records")

    op.drop_index("ix_termination_histories_org_created", table_name="termination_histories")
    op.drop_index("ix_termination_histories_contract_id", table_name="termination_histories")
    op.drop_table("termination_histories")

