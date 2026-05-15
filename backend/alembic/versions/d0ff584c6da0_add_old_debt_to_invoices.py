"""add_old_debt_to_invoices

Revision ID: d0ff584c6da0
Revises: 048823e99445
Create Date: 2026-05-15 21:38:04.928651

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd0ff584c6da0'
down_revision = '048823e99445'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('invoices', sa.Column('old_debt', sa.BigInteger(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('invoices', 'old_debt')
