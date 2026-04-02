"""Compatibility wrapper for legacy service imports.

Business logic now lives in app.application.use_cases.
"""

__all__ = [
    "OllamaService",
    "OllamaServiceError",
    "OllamaConfigurationError",
    "OllamaRequestError",
]


def __getattr__(name: str):
    if name not in {
        "OllamaService",
        "OllamaServiceError",
        "OllamaConfigurationError",
        "OllamaRequestError",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from app.application.use_cases.ollama_service import (
        OllamaConfigurationError,
        OllamaRequestError,
        OllamaService,
        OllamaServiceError,
    )

    return {
        "OllamaService": OllamaService,
        "OllamaServiceError": OllamaServiceError,
        "OllamaConfigurationError": OllamaConfigurationError,
        "OllamaRequestError": OllamaRequestError,
    }[name]
