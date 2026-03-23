"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

__all__ = [
    "CharacterService",
]


def __getattr__(name: str):
    if name != "CharacterService":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from app.application.use_cases.character_service import CharacterService
    return CharacterService
