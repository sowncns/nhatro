"""add_vehicle_count_to_contracts

Revision ID: 67891864d92a
Revises: 002_add_missing_indexes
Create Date: 2026-05-15 20:18:46.042602

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '67891864d92a'
down_revision = '002_add_missing_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('contracts', sa.Column('vehicle_count', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('contracts', 'vehicle_count')
