"""Package des services métier - Imports centralisés"""

from .combat_service import CombatService
from .combatant_service import CombatantService
from .group_service import GroupService
from .template_service import TemplateService

# Exposition des services
__all__ = [
    'CombatService',
    'CombatantService',
    'GroupService',
    'TemplateService'
]