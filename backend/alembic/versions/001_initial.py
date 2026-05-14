"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This migration is handled by SQLAlchemy create_all in development.
    # In production, use alembic to manage migrations properly.
    # 
    # The models in app/models/models.py define the full schema.
    # Run: alembic upgrade head
    # 
    # For production setup:
    # 1. Set DATABASE_URL in .env
    # 2. Run: cd backend && alembic upgrade head
    # 3. Run: python -m app.utils.seed_data (for sample data)
    pass


def downgrade() -> None:
    pass
