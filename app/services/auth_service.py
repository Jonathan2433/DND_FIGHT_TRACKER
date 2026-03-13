"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

from app.application.use_cases.auth_service import AuthService

__all__ = [
    "AuthService",
]
