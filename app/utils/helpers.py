"""Fonctions utilitaires pour l'application D&D Combat Tracker"""
from werkzeug.utils import secure_filename
from app.utils.constants import ALLOWED_EXTENSIONS


def allowed_file(filename):
    """Vérifier si l'extension de fichier est autorisée"""
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_current_actor(combat):
    """Récupérer l'acteur actuel du combat (en tenant compte des morts/fuyards)"""
    combatants = sorted(
        [c for c in combat.combatants if not c.is_hidden],
        key=lambda x: x.initiative,
        reverse=True
    )

    # Vérification de sécurité
    if not combatants or combat.current_turn >= len(combatants):
        return None  # Aucun acteur valide trouvé

    return combatants[combat.current_turn]


def format_duration(seconds):
    """Formater une durée en secondes vers MM:SS"""
    if not seconds:
        return "00:00"

    total_seconds = int(seconds)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def calculate_hp_percentage(current_hp, max_hp):
    """Calculer le pourcentage de HP restant"""
    if max_hp <= 0:
        return 0
    return (current_hp / max_hp) * 100


def get_hp_status_text(current_hp, max_hp):
    """Obtenir le texte de statut basé sur les HP"""
    if current_hp <= 0:
        return "💀 Mort"

    ratio = current_hp / max_hp
    if ratio > 0.75:
        return "🟢 En pleine forme"
    elif ratio > 0.4:
        return "🟡 Blessé"
    elif ratio > 0.1:
        return "🟠 Gravement blessé"
    else:
        return "🔴 À l'agonie"


def get_hp_bar_class(current_hp, max_hp):
    """Obtenir la classe CSS pour la barre de HP"""
    if current_hp <= 0:
        return "hp-red"

    ratio = current_hp / max_hp
    if ratio > 0.75:
        return "hp-green"
    elif ratio > 0.4:
        return "hp-yellow"
    elif ratio > 0.1:
        return "hp-orange"
    else:
        return "hp-red"


def parse_conditions(conditions_string):
    """Parser une chaîne de conditions en liste"""
    if not conditions_string:
        return []
    return [cond.strip() for cond in conditions_string.split(",") if cond.strip()]


def format_conditions(conditions_list):
    """Formater une liste de conditions en chaîne"""
    if not conditions_list:
        return ""
    return ",".join(conditions_list)


def get_proficiency_bonus(level):
    """Calculer le bonus de maîtrise basé sur le niveau"""
    if level <= 4:
        return 2
    elif level <= 8:
        return 3
    elif level <= 12:
        return 4
    elif level <= 16:
        return 5
    else:
        return 6


def calculate_ability_modifier(ability_score):
    """Calculer le modificateur d'une caractéristique"""
    return (ability_score - 10) // 2


def get_initiative_order(combatants):
    """Obtenir l'ordre d'initiative trié"""
    return sorted(
        [c for c in combatants if not c.is_hidden],
        key=lambda x: x.initiative,
        reverse=True
    )


def safe_filename(filename):
    """Sécuriser un nom de fichier"""
    return secure_filename(filename) if filename else None