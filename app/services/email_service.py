"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

from app.application.use_cases.email_service import EmailService

__all__ = [
    "EmailService",
]
