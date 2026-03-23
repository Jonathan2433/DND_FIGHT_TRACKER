"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

__all__ = [
    "EmailService",
]


def __getattr__(name: str):
    if name != "EmailService":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from app.application.use_cases.email_service import EmailService
    return EmailService
