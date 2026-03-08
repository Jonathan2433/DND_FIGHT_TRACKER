"""Package utilitaires - Imports pour faciliter l'usage"""

from .constants import (
    MONSTER_TEMPLATES,
    CONDITIONS_LIST,
    CONDITIONS_DESCRIPTIONS,
    COMBATANT_TYPES,
    ALLOWED_EXTENSIONS,
    COMBAT_ACTION_TYPES,
    ENCOUNTER_DIFFICULTIES
)

from .helpers import (
    allowed_file,
    get_current_actor,
    format_duration,
    calculate_hp_percentage,
    get_hp_status_text,
    get_hp_bar_class,
    parse_conditions,
    format_conditions,
    get_proficiency_bonus,
    calculate_ability_modifier,
    get_initiative_order,
    safe_filename
)

# Exposition des fonctions et constantes
__all__ = [
    # Constantes
    'MONSTER_TEMPLATES',
    'CONDITIONS_LIST',
    'CONDITIONS_DESCRIPTIONS',
    'COMBATANT_TYPES',
    'ALLOWED_EXTENSIONS',
    'COMBAT_ACTION_TYPES',
    'ENCOUNTER_DIFFICULTIES',

    # Fonctions utilitaires
    'allowed_file',
    'get_current_actor',
    'format_duration',
    'calculate_hp_percentage',
    'get_hp_status_text',
    'get_hp_bar_class',
    'parse_conditions',
    'format_conditions',
    'get_proficiency_bonus',
    'calculate_ability_modifier',
    'get_initiative_order',
    'safe_filename'
]