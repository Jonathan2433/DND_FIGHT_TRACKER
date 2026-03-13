"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

from app.application.use_cases.xp_service import XPService

__all__ = [
    "XPService",
]
