"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

from app.application.use_cases.combatant_service import CombatantService

__all__ = [
    "CombatantService",
]
