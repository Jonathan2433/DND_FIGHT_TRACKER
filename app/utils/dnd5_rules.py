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
    "Barbare": {
        "hit_die": 12,
        "saving_throws": ["force", "constitution"],
        "description": "Combattant sauvage et endurant, le barbare excelle en melee grace a sa rage et sa resistance.",
    },
    "Barde": {
        "hit_die": 8,
        "saving_throws": ["dexterite", "charisme"],
        "description": "Artiste polyvalent, le barde soutient le groupe avec ses inspirations, sa magie et ses competences sociales.",
    },
    "Clerc": {
        "hit_die": 8,
        "saving_throws": ["sagesse", "charisme"],
        "description": "Lanceur de sorts divin, le clerc soigne, protege ses allies et invoque la puissance de sa divinite.",
    },
    "Druide": {
        "hit_die": 8,
        "saving_throws": ["intelligence", "sagesse"],
        "description": "Gardien de la nature, le druide maitrise les sorts elementaires et la metamorphose animale.",
    },
    "Ensorceleur": {
        "hit_die": 6,
        "saving_throws": ["constitution", "charisme"],
        "description": "Magicien instinctif, l'ensorceleur puise sa puissance dans un heritage magique inne et modele ses sorts.",
    },
    "Guerrier": {
        "hit_die": 10,
        "saving_throws": ["force", "constitution"],
        "description": "Specialiste des armes et armures, le guerrier est fiable en premiere ligne et tres adaptable.",
    },
    "Magicien": {
        "hit_die": 6,
        "saving_throws": ["intelligence", "sagesse"],
        "description": "Erudit des arcanes, le magicien possede la plus large palette de sorts utilitaires et offensifs.",
    },
    "Moine": {
        "hit_die": 8,
        "saving_throws": ["force", "dexterite"],
        "description": "Adepte du ki, le moine allie mobilite, precision et techniques martiales spectaculaires.",
    },
    "Paladin": {
        "hit_die": 10,
        "saving_throws": ["sagesse", "charisme"],
        "description": "Champion sacre, le paladin combine defense, soutien et gros degats grace a ses chatiments divins.",
    },
    "Rodeur": {
        "hit_die": 10,
        "saving_throws": ["force", "dexterite"],
        "description": "Eclaireur des terres sauvages, le rodeur piste ses proies et combat avec precision a distance ou au contact.",
    },
    "Roublard": {
        "hit_die": 8,
        "saving_throws": ["dexterite", "intelligence"],
        "description": "Expert de l'infiltration, le roublard frappe juste au bon moment et excelle hors combat.",
    },
    "Occultiste": {
        "hit_die": 8,
        "saving_throws": ["sagesse", "charisme"],
        "description": "L'occultiste tire sa magie d'un pacte surnaturel, avec des pouvoirs atypiques et des invocations.",
    },
}

ABILITY_NAMES = ["force", "dexterite", "constitution", "intelligence", "sagesse", "charisme"]

BACKGROUND_RULES = {
    "Acolyte": {
        "skills": ["Intuition", "Religion"],
        "feature": "Abri des fideles",
        "description": "Vous avez servi un temple et pouvez obtenir aide, soins simples et refuge aupres des lieux de culte de votre foi.",
    },
    "Artisan de guilde": {
        "skills": ["Intuition", "Persuasion"],
        "feature": "Membre de guilde",
        "description": "Votre guilde vous ouvre des portes commerciales, un reseau de contacts et un soutien logistique de base.",
    },
    "Charlatan": {
        "skills": ["Tromperie", "Escamotage"],
        "feature": "Identite de couverture",
        "description": "Vous maintenez une fausse identite et savez obtenir de petits services en jouant votre role.",
    },
    "Criminel": {
        "skills": ["Tromperie", "Discretion"],
        "feature": "Contact criminel",
        "description": "Vous connaissez un contact fiable dans les bas-fonds pour faire passer des messages et denicher des informations.",
    },
    "Ermite": {
        "skills": ["Medecine", "Religion"],
        "feature": "Decouverte",
        "description": "Votre retrait du monde vous a offert une revelation majeure que vous pouvez exploiter en jeu.",
    },
    "Heros du peuple": {
        "skills": ["Dressage", "Survie"],
        "feature": "Hospitalite rustique",
        "description": "Les gens simples vous hebergent volontiers et vous protegent tant que vous ne les mettez pas en danger direct.",
    },
    "Marin": {
        "skills": ["Athletisme", "Perception"],
        "feature": "Passage sur navire",
        "description": "Vous pouvez generalement obtenir un passage gratuit sur un navire civil pour vous et vos compagnons.",
    },
    "Noble": {
        "skills": ["Histoire", "Persuasion"],
        "feature": "Position de privilege",
        "description": "Votre titre ouvre des portes dans les cercles de pouvoir et facilite l'obtention d'audiences officielles.",
    },
    "Sage": {
        "skills": ["Arcanes", "Histoire"],
        "feature": "Chercheur",
        "description": "Vous savez ou trouver savoirs et references, et vers qui vous tourner pour une reponse erudite.",
    },
    "Soldat": {
        "skills": ["Athletisme", "Intimidation"],
        "feature": "Grade militaire",
        "description": "Votre passe militaire vous donne autorite sur des soldats de rang inferieur et un acces a des garnisons alliees.",
    },
}


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
