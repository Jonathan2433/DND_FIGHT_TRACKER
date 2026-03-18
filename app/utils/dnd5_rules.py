"""Règles simplifiées DnD 5e (version 2024) pour le funnel de création de personnage."""

STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]

# En 2024, les bonus de caractéristiques ne sont plus liés à l'espèce.
# On conserve cette structure pour compatibilité d'affichage et de code existant.
RACE_BONUSES = {
    "Aasimar": {},
    "Dragonborn": {},
    "Dwarf": {},
    "Elf": {},
    "Gnome": {},
    "Goliath": {},
    "Halfling": {},
    "Human": {},
    "Orc": {},
    "Tiefling": {},
}

CLASS_RULES = {
    "Barbarian": {
        "hit_die": 12,
        "saving_throws": ["force", "constitution"],
        "description": "Combattant sauvage et endurant, le barbare excelle en melee grace a sa rage et sa resistance.",
    },
    "Bard": {
        "hit_die": 8,
        "saving_throws": ["dexterite", "charisme"],
        "description": "Artiste polyvalent, le barde soutient le groupe avec ses inspirations, sa magie et ses competences sociales.",
    },
    "Cleric": {
        "hit_die": 8,
        "saving_throws": ["sagesse", "charisme"],
        "description": "Lanceur de sorts divin, le clerc soigne, protege ses allies et invoque la puissance de sa divinite.",
    },
    "Druid": {
        "hit_die": 8,
        "saving_throws": ["intelligence", "sagesse"],
        "description": "Gardien de la nature, le druide maitrise les sorts elementaires et la metamorphose animale.",
    },
    "Fighter": {
        "hit_die": 10,
        "saving_throws": ["force", "constitution"],
        "description": "Specialiste des armes et armures, le guerrier est fiable en premiere ligne et tres adaptable.",
    },
    "Monk": {
        "hit_die": 8,
        "saving_throws": ["force", "dexterite"],
        "description": "Adepte du ki, le moine allie mobilite, precision et techniques martiales spectaculaires.",
    },
    "Paladin": {
        "hit_die": 10,
        "saving_throws": ["sagesse", "charisme"],
        "description": "Champion sacre, le paladin combine defense, soutien et gros degats grace a ses chatiments divins.",
    },
    "Ranger": {
        "hit_die": 10,
        "saving_throws": ["force", "dexterite"],
        "description": "Eclaireur des terres sauvages, le rodeur piste ses proies et combat avec precision a distance ou au contact.",
    },
    "Rogue": {
        "hit_die": 8,
        "saving_throws": ["dexterite", "intelligence"],
        "description": "Expert de l'infiltration, le roublard frappe juste au bon moment et excelle hors combat.",
    },
    "Sorcerer": {
        "hit_die": 6,
        "saving_throws": ["constitution", "charisme"],
        "description": "Magicien instinctif, l'ensorceleur puise sa puissance dans un heritage magique inne et modele ses sorts.",
    },
    "Warlock": {
        "hit_die": 8,
        "saving_throws": ["sagesse", "charisme"],
        "description": "L'occultiste tire sa magie d'un pacte surnaturel, avec des pouvoirs atypiques et des invocations.",
    },
    "Wizard": {
        "hit_die": 6,
        "saving_throws": ["intelligence", "sagesse"],
        "description": "Erudit des arcanes, le magicien possede la plus large palette de sorts utilitaires et offensifs.",
    },
}

ABILITY_NAMES = ["force", "dexterite", "constitution", "intelligence", "sagesse", "charisme"]

BACKGROUND_RULES = {
    "Acolyte": {
        "skills": ["Insight", "Religion"],
        "feature": "Appel divin",
        "description": "Origine religieuse : vous etes forme aux rites et a l'etude du sacre.",
        "ability_options": ["intelligence", "sagesse", "charisme"],
    },
    "Artisan": {
        "skills": ["Investigation", "Persuasion"],
        "feature": "Savoir-faire",
        "description": "Vous venez d'un metier manuel ou d'atelier et savez valoriser votre expertise.",
        "ability_options": ["force", "dexterite", "intelligence"],
    },
    "Charlatan": {
        "skills": ["Deception", "Sleight of Hand"],
        "feature": "Arnaqueur de talent",
        "description": "Vous maitrisez les faux-semblants, les impostures et les manipulations sociales.",
        "ability_options": ["dexterite", "constitution", "charisme"],
    },
    "Criminal": {
        "skills": ["Sleight of Hand", "Stealth"],
        "feature": "Réseau du milieu",
        "description": "Vous connaissez les codes des bas-fonds et savez operer discretement.",
        "ability_options": ["dexterite", "constitution", "intelligence"],
    },
    "Entertainer": {
        "skills": ["Acrobatics", "Performance"],
        "feature": "Art de la scene",
        "description": "Vous savez captiver un public et faire de votre presence un atout.",
        "ability_options": ["force", "dexterite", "charisme"],
    },
    "Farmer": {
        "skills": ["Animal Handling", "Nature"],
        "feature": "Vie rurale",
        "description": "Vous etes rompu aux travaux du quotidien et a la vie au grand air.",
        "ability_options": ["force", "constitution", "sagesse"],
    },
    "Guard": {
        "skills": ["Athletics", "Perception"],
        "feature": "Vigilance",
        "description": "Vous etes habitue a proteger, patrouiller et reagir aux menaces.",
        "ability_options": ["force", "intelligence", "sagesse"],
    },
    "Guide": {
        "skills": ["Stealth", "Survival"],
        "feature": "Connaissance du terrain",
        "description": "Vous savez mener un groupe en milieu hostile et trouver votre route.",
        "ability_options": ["dexterite", "constitution", "sagesse"],
    },
    "Hermit": {
        "skills": ["Medicine", "Religion"],
        "feature": "Recul et introspection",
        "description": "Votre retraite vous a apporte discipline, endurance et sagesse interieure.",
        "ability_options": ["constitution", "sagesse", "charisme"],
    },
    "Merchant": {
        "skills": ["Animal Handling", "Persuasion"],
        "feature": "Sens des affaires",
        "description": "Vous savez negocier, estimer et tirer profit des opportunites.",
        "ability_options": ["constitution", "intelligence", "charisme"],
    },
    "Noble": {
        "skills": ["History", "Persuasion"],
        "feature": "Etiquette de cour",
        "description": "Vous evoluez avec aisance dans les cercles d'influence et de pouvoir.",
        "ability_options": ["force", "intelligence", "charisme"],
    },
    "Sage": {
        "skills": ["Arcana", "History"],
        "feature": "Erudition",
        "description": "Vous avez passe votre vie a compiler, etudier et transmettre le savoir.",
        "ability_options": ["constitution", "intelligence", "sagesse"],
    },
    "Sailor": {
        "skills": ["Perception", "Acrobatics"],
        "feature": "Marin aguerri",
        "description": "Vous connaissez les navires, les tempetes et la vie de pont.",
        "ability_options": ["force", "dexterite", "sagesse"],
    },
    "Scribe": {
        "skills": ["Investigation", "Perception"],
        "feature": "Memoire ecrite",
        "description": "Vous etes forme aux archives, aux manuscrits et aux details cruciaux.",
        "ability_options": ["dexterite", "intelligence", "sagesse"],
    },
    "Soldier": {
        "skills": ["Athletics", "Intimidation"],
        "feature": "Formation militaire",
        "description": "Vous avez appris la discipline, la tactique et le travail d'unite.",
        "ability_options": ["force", "dexterite", "constitution"],
    },
    "Wayfarer": {
        "skills": ["Insight", "Stealth"],
        "feature": "Voyageur",
        "description": "Vous avez l'habitude de vivre sur les routes et d'improviser partout.",
        "ability_options": ["dexterite", "sagesse", "charisme"],
    },
}


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def ability_modifier(score):
    return (score - 10) // 2


def _resolve_background_bonuses(form_data, background_name):
    background_rule = BACKGROUND_RULES.get(background_name, {})
    allowed = set(background_rule.get("ability_options", []))

    requested_bonus = {}
    for ability in ABILITY_NAMES:
        raw_value = form_data.get(f"{ability}_bg_bonus", 0)
        bonus_value = _clamp(int(raw_value), 0, 2)
        requested_bonus[ability] = bonus_value if ability in allowed else 0

    spent_points = sum(requested_bonus.values())

    # Compatibilité : si rien n'est envoyé, appliquer +1/+1/+1 sur les scores autorisés.
    if spent_points == 0 and allowed:
        for ability in background_rule.get("ability_options", []):
            requested_bonus[ability] = 1
        return requested_bonus

    # Normaliser pour respecter le budget 2024 (3 points max, max +2 par score).
    if spent_points > 3:
        overflow = spent_points - 3
        for ability in ABILITY_NAMES:
            if overflow <= 0:
                break
            reducible = min(overflow, requested_bonus[ability])
            requested_bonus[ability] -= reducible
            overflow -= reducible

    return requested_bonus


def resolve_character_creation(form_data):
    """Calcule les stats finales et les valeurs dérivées selon les règles 2024."""
    level = _clamp(int(form_data.get("level", 1)), 1, 20)
    race = form_data.get("race", "Human")
    character_class = form_data.get("character_class", "Fighter")
    background_name = form_data.get("background_story", "Acolyte")

    base_scores = {}
    for ability in ABILITY_NAMES:
        base_value = int(form_data.get(f"{ability}_base", form_data.get(ability, 10)))
        base_scores[ability] = _clamp(base_value, 1, 20)

    background_bonus = _resolve_background_bonuses(form_data, background_name)
    final_scores = {
        ability: _clamp(base_scores[ability] + background_bonus.get(ability, 0), 1, 20)
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
