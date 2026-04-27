"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

__all__ = [
    "CampaignService",
]


def __getattr__(name: str):
    if name != "CampaignService":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from app.application.use_cases.campaign_service import CampaignService
    return CampaignService
