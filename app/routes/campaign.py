"""Compatibility wrapper for legacy route imports.

HTTP route implementation now lives in app.web.routes.
"""

from app.web.routes.campaign import *  # noqa: F401,F403
