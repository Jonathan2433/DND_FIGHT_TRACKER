"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

from app.application.use_cases.group_service import GroupService

__all__ = [
    "GroupService",
]
