"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

__all__ = [
    "CombatService",
]


def __getattr__(name: str):
    if name != "CombatService":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from app.application.use_cases.combat_service import CombatService
    return CombatService
