"""Legacy route package kept for backward compatibility.
Use app.web.routes as the primary web layer.
"""

from app.web.routes import BLUEPRINTS, register_blueprints

__all__ = ["register_blueprints", "BLUEPRINTS"]
