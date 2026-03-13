"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

from app.application.use_cases.template_service import TemplateService

__all__ = [
    "TemplateService",
]
