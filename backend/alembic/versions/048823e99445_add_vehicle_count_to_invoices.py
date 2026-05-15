"""add_vehicle_count_to_invoices

Revision ID: 048823e99445
Revises: 67891864d92a
Create Date: 2026-05-15 20:58:41.126193

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '048823e99445'
down_revision = '67891864d92a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('invoices', sa.Column('vehicle_count', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('invoices', 'vehicle_count')
