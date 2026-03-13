"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

from app.application.use_cases.character_service import CharacterService

__all__ = [
    "CharacterService",
]
