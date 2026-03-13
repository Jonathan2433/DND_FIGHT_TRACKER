"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

from app.application.use_cases.story_arc_service import StoryArcService

__all__ = [
    "StoryArcService",
]
