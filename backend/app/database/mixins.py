"""Database Mixins for common patterns"""
from datetime import datetime
from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.sql import func


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    archived_at = Column(DateTime(timezone=True), nullable=True, index=True)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)

    def soft_delete(self):
        """Mark record as deleted"""
        self.is_archived = True
        self.archived_at = datetime.utcnow()

    def restore(self):
        """Restore soft-deleted record"""
        self.is_archived = False
        self.archived_at = None


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AuditMixin(TimestampMixin, SoftDeleteMixin):
    """Combined mixin for timestamp and soft delete"""
    pass
