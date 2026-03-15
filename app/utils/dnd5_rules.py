"""Règles simplifiées DnD 5e pour le funnel de création de personnage."""

STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]

RACE_BONUSES = {
    "Humain": {
        "force": 1,
        "dexterite": 1,
        "constitution": 1,
        "intelligence": 1,
        "sagesse": 1,
        "charisme": 1,
    },
    "Elfe": {"dexterite": 2},
    "Nain": {"constitution": 2},
    "Halfelin": {"dexterite": 2},
    "Drakeide": {"force": 2, "charisme": 1},
    "Gnome": {"intelligence": 2},
    "Demi-elfe": {"charisme": 2, "dexterite": 1, "constitution": 1},
    "Demi-orc": {"force": 2, "constitution": 1},
    "Tieffelin": {"charisme": 2, "intelligence": 1},
}

CLASS_RULES = {
    "Barbare": {"hit_die": 12, "saving_throws": ["force", "constitution"]},
    "Barde": {"hit_die": 8, "saving_throws": ["dexterite", "charisme"]},
    "Clerc": {"hit_die": 8, "saving_throws": ["sagesse", "charisme"]},
    "Druide": {"hit_die": 8, "saving_throws": ["intelligence", "sagesse"]},
    "Ensorceleur": {"hit_die": 6, "saving_throws": ["constitution", "charisme"]},
    "Guerrier": {"hit_die": 10, "saving_throws": ["force", "constitution"]},
    "Magicien": {"hit_die": 6, "saving_throws": ["intelligence", "sagesse"]},
    "Moine": {"hit_die": 8, "saving_throws": ["force", "dexterite"]},
    "Paladin": {"hit_die": 10, "saving_throws": ["sagesse", "charisme"]},
    "Rodeur": {"hit_die": 10, "saving_throws": ["force", "dexterite"]},
    "Roublard": {"hit_die": 8, "saving_throws": ["dexterite", "intelligence"]},
    "Occultiste": {"hit_die": 8, "saving_throws": ["sagesse", "charisme"]},
}

ABILITY_NAMES = ["force", "dexterite", "constitution", "intelligence", "sagesse", "charisme"]


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def ability_modifier(score):
    return (score - 10) // 2


def resolve_character_creation(form_data):
    """Calcule les stats finales et les valeurs dérivées selon race/classe."""
    level = _clamp(int(form_data.get("level", 1)), 1, 20)
    race = form_data.get("race", "Humain")
    character_class = form_data.get("character_class", "Guerrier")

    base_scores = {}
    for ability in ABILITY_NAMES:
        base_value = int(form_data.get(f"{ability}_base", form_data.get(ability, 10)))
        base_scores[ability] = _clamp(base_value, 1, 20)

    race_bonus = RACE_BONUSES.get(race, {})
    final_scores = {
        ability: _clamp(base_scores[ability] + race_bonus.get(ability, 0), 1, 20)
        for ability in ABILITY_NAMES
    }

    class_rule = CLASS_RULES.get(character_class, {"hit_die": 8, "saving_throws": []})
    hit_die = class_rule["hit_die"]
    constitution_mod = ability_modifier(final_scores["constitution"])
    average_gain = (hit_die // 2) + 1
    hp_max = max(1, hit_die + constitution_mod + (level - 1) * (average_gain + constitution_mod))

    dex_modifier = ability_modifier(final_scores["dexterite"])
    ac_base = int(form_data.get("ac_base", max(10, 10 + dex_modifier)))

    payload = {
        "race": race,
        "character_class": character_class,
        "level": level,
        "hp_max": hp_max,
        "ac_base": ac_base,
        "initiative_bonus": dex_modifier,
    }

    for ability, value in final_scores.items():
        payload[ability] = value

    saving_throws = set(class_rule["saving_throws"])
    for ability in ABILITY_NAMES:
        payload[f"maitrise_{ability}"] = ability in saving_throws

    return payload
