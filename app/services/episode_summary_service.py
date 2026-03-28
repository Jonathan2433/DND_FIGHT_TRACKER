"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

__all__ = [
    'EpisodeSummaryService',
    'EpisodeSummaryError',
    'EpisodeSummaryAccessError',
    'EpisodeSummaryAlreadyRunningError',
    'EpisodeSummaryGenerationError',
]


def __getattr__(name: str):
    if name not in {
        'EpisodeSummaryService',
        'EpisodeSummaryError',
        'EpisodeSummaryAccessError',
        'EpisodeSummaryAlreadyRunningError',
        'EpisodeSummaryGenerationError',
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from app.application.use_cases.episode_summary_service import (
        EpisodeSummaryAccessError,
        EpisodeSummaryAlreadyRunningError,
        EpisodeSummaryError,
        EpisodeSummaryGenerationError,
        EpisodeSummaryService,
    )

    return {
        'EpisodeSummaryService': EpisodeSummaryService,
        'EpisodeSummaryError': EpisodeSummaryError,
        'EpisodeSummaryAccessError': EpisodeSummaryAccessError,
        'EpisodeSummaryAlreadyRunningError': EpisodeSummaryAlreadyRunningError,
        'EpisodeSummaryGenerationError': EpisodeSummaryGenerationError,
    }[name]
