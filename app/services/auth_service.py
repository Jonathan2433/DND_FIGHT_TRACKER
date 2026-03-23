"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

__all__ = [
    "AuthService",
]


def __getattr__(name: str):
    if name != "AuthService":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from app.application.use_cases.auth_service import AuthService
    return AuthService
