"""Compatibility package for legacy service import paths.

Intentionally avoids re-exporting service classes to prevent circular imports.
Use explicit module imports instead, e.g.:
    from app.services.auth_service import AuthService
"""

__all__: list[str] = []
