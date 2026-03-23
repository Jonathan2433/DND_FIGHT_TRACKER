"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

__all__ = [
    "GroupService",
]


def __getattr__(name: str):
    if name != "GroupService":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from app.application.use_cases.group_service import GroupService
    return GroupService
