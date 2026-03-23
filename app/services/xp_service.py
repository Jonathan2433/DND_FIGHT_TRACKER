"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

__all__ = [
    "XPService",
]


def __getattr__(name: str):
    if name != "XPService":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from app.application.use_cases.xp_service import XPService
    return XPService
