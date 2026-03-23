"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

__all__ = [
    "StoryArcService",
]


def __getattr__(name: str):
    if name != "StoryArcService":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from app.application.use_cases.story_arc_service import StoryArcService
    return StoryArcService
