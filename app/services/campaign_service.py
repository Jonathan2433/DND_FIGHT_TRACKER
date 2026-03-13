"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

from app.application.use_cases.campaign_service import CampaignService

__all__ = [
    "CampaignService",
]
