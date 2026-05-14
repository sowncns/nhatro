"""Compatibility re-export for legacy imports.

The ORM models live in app.database.models. Some services still import
app.models.models, so keep this module as the single compatibility layer.
"""
from app.database.models import *  # noqa: F401,F403
