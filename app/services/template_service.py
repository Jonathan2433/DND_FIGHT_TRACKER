"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

__all__ = [
    "TemplateService",
]


def __getattr__(name: str):
    if name != "TemplateService":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from app.application.use_cases.template_service import TemplateService
    return TemplateService
