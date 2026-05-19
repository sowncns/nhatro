"""merge_payment_and_soft_delete

Revision ID: f0924b97c02a
Revises: 003_add_soft_delete_constraints, 013_payment_confirmation
Create Date: 2026-05-19 17:44:05.119709

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f0924b97c02a'
down_revision = ('003_add_soft_delete_constraints', '013_payment_confirmation')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
