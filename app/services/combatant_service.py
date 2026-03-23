"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

__all__ = [
    "CombatantService",
]


def __getattr__(name: str):
    if name != "CombatantService":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from app.application.use_cases.combatant_service import CombatantService
    return CombatantService
