"""Règles simplifiées DnD 5e (version 2024) pour le funnel de création de personnage."""

STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]
POINT_BUY_COSTS = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
POINT_BUY_BUDGET = 27

CLASS_LABELS_FR = {
    "Barbarian": "Barbare",
    "Bard": "Barde",
    "Cleric": "Clerc",
    "Druid": "Druide",
    "Fighter": "Guerrier",
    "Monk": "Moine",
    "Paladin": "Paladin",
    "Ranger": "Rôdeur",
    "Rogue": "Roublard",
    "Sorcerer": "Ensorceleur",
    "Warlock": "Occultiste",
    "Wizard": "Magicien",
}

SPECIES_LABELS_FR = {
    "Aasimar": "Aasimar",
    "Dragonborn": "Drakéide",
    "Dwarf": "Nain",
    "Elf": "Elfe",
    "Gnome": "Gnome",
    "Goliath": "Goliath",
    "Halfling": "Halfelin",
    "Human": "Humain",
    "Orc": "Orc",
    "Tiefling": "Tieffelin",
}

BACKGROUND_LABELS_FR = {
    "Acolyte": "Acolyte",
    "Artisan": "Artisan",
    "Charlatan": "Charlatan",
    "Criminal": "Criminel",
    "Entertainer": "Artiste",
    "Farmer": "Fermier",
    "Guard": "Garde",
    "Guide": "Guide",
    "Hermit": "Ermite",
    "Merchant": "Marchand",
    "Noble": "Noble",
    "Sage": "Sage",
    "Sailor": "Marin",
    "Scribe": "Scribe",
    "Soldier": "Soldat",
    "Wayfarer": "Voyageur",
}

ALIGNMENTS_FR = [
    {"value": "", "label": "Non précisé", "description": "Aucun alignement défini pour l'instant."},
    {"value": "Loyal Bon", "label": "Loyal Bon", "description": "Respecte les lois et agit pour le bien commun."},
    {"value": "Neutre Bon", "label": "Neutre Bon", "description": "Cherche surtout à faire le bien, avec souplesse."},
    {"value": "Chaotique Bon", "label": "Chaotique Bon", "description": "Privilégie la liberté individuelle au service du bien."},
    {"value": "Loyal Neutre", "label": "Loyal Neutre", "description": "Suit les règles, l'ordre et ses principes avant tout."},
    {"value": "Neutre", "label": "Neutre", "description": "Recherche l'équilibre ou agit selon le contexte."},
    {"value": "Chaotique Neutre", "label": "Chaotique Neutre", "description": "Suit avant tout son indépendance et son instinct."},
    {"value": "Loyal Mauvais", "label": "Loyal Mauvais", "description": "Utilise l'ordre et les règles pour dominer ou exploiter."},
    {"value": "Neutre Mauvais", "label": "Neutre Mauvais", "description": "Poursuit ses intérêts sans scrupules particuliers."},
    {"value": "Chaotique Mauvais", "label": "Chaotique Mauvais", "description": "Sème la destruction selon ses pulsions et sa cruauté."},
]

TERM_TRANSLATIONS_FR = {
    "light": "légères",
    "medium": "intermédiaires",
    "heavy": "lourdes",
    "shields": "boucliers",
    "simple": "simples",
    "martial": "martiales",
    "shortsword": "épée courte",
    "hand crossbow": "arbalète de poing",
    "longsword": "épée longue",
    "rapier": "rapière",
    "Insight": "Intuition",
    "Religion": "Religion",
    "Investigation": "Investigation",
    "Persuasion": "Persuasion",
    "Deception": "Tromperie",
    "Sleight of Hand": "Escamotage",
    "Stealth": "Discrétion",
    "Acrobatics": "Acrobaties",
    "Performance": "Représentation",
    "Animal Handling": "Dressage",
    "Nature": "Nature",
    "Athletics": "Athlétisme",
    "Perception": "Perception",
    "Survival": "Survie",
    "Medicine": "Médecine",
    "History": "Histoire",
    "Arcana": "Arcanes",
    "Intimidation": "Intimidation",
    "Calligrapher’s Supplies": "Matériel de calligraphe",
    "Thieves’ Tools": "Outils de voleur",
    "Magic Initiate (Cleric)": "Initiation à la magie (Clerc)",
    "Crafter": "Artisanat",
    "Skilled": "Compétent",
    "Alert": "Alerte",
    "Musician": "Musicien",
    "Tough": "Robuste",
    "Magic Initiate (Druid)": "Initiation à la magie (Druide)",
    "Healer": "Guérisseur",
    "Lucky": "Chanceux",
    "Magic Initiate (Wizard)": "Initiation à la magie (Magicien)",
    "Tavern Brawler": "Bagarreur de taverne",
    "Savage Attacker": "Attaquant sauvage",
    "Darkvision": "Vision dans le noir",
    "Healing Hands": "Mains guérisseuses",
    "Celestial Revelation": "Révélation céleste",
    "Draconic Ancestry": "Ascendance draconique",
    "Breath Weapon": "Souffle draconique",
    "Damage Resistance": "Résistance aux dégâts",
    "Dwarven Resilience": "Résilience naine",
    "Dwarven Toughness": "Robustesse naine",
    "Stonecunning": "Maîtrise de la pierre",
    "Keen Senses": "Sens aiguisés",
    "Fey Ancestry": "Ascendance féerique",
    "Trance": "Transe",
    "Gnomish Cunning": "Ruse gnome",
    "Gnomish Lineage": "Lignage gnome",
    "Large Form": "Grande carrure",
    "Powerful Build": "Constitution puissante",
    "Giant Ancestry": "Ascendance des géants",
    "Brave": "Bravoure",
    "Halfling Nimbleness": "Agilité halfeline",
    "Luck": "Chance",
    "Resourceful": "Débrouillard",
    "Skillful": "Polyvalent",
    "Versatile": "Adaptable",
    "Adrenaline Rush": "Montée d'adrénaline",
    "Relentless Endurance": "Endurance implacable",
    "Fiendish Legacy": "Héritage infernal",
    "Otherworldly Presence": "Présence d'outre-monde",
}

# En 2024, les bonus de caractéristiques ne sont plus liés à l'espèce.
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

SPECIES_RULES = {
    "Aasimar": {
        "size": "Moyenne",
        "speed": 30,
        "proficiencies": [],
        "traits": ["Darkvision", "Healing Hands", "Celestial Revelation"],
    },
    "Dragonborn": {
        "size": "Moyenne",
        "speed": 30,
        "proficiencies": [],
        "traits": ["Darkvision", "Draconic Ancestry", "Breath Weapon", "Damage Resistance"],
    },
    "Dwarf": {
        "size": "Moyenne",
        "speed": 30,
        "proficiencies": [],
        "traits": ["Darkvision", "Dwarven Resilience", "Dwarven Toughness", "Stonecunning"],
    },
    "Elf": {
        "size": "Moyenne",
        "speed": 30,
        "proficiencies": [],
        "traits": ["Darkvision", "Keen Senses", "Fey Ancestry", "Trance"],
    },
    "Gnome": {
        "size": "Petite",
        "speed": 30,
        "proficiencies": [],
        "traits": ["Darkvision", "Gnomish Cunning", "Gnomish Lineage"],
    },
    "Goliath": {
        "size": "Moyenne",
        "speed": 35,
        "proficiencies": [],
        "traits": ["Large Form", "Powerful Build", "Giant Ancestry"],
    },
    "Halfling": {
        "size": "Petite",
        "speed": 30,
        "proficiencies": [],
        "traits": ["Brave", "Halfling Nimbleness", "Luck"],
    },
    "Human": {
        "size": "Moyenne",
        "speed": 30,
        "proficiencies": [],
        "traits": ["Resourceful", "Skillful", "Versatile"],
        "extra_origin_feat": True,
    },
    "Orc": {
        "size": "Moyenne",
        "speed": 30,
        "proficiencies": [],
        "traits": ["Adrenaline Rush", "Darkvision", "Relentless Endurance"],
    },
    "Tiefling": {
        "size": "Moyenne",
        "speed": 30,
        "proficiencies": [],
        "traits": ["Darkvision", "Fiendish Legacy", "Otherworldly Presence"],
    },
}

COMMON_LANGUAGES = [
    "Commun",
    "Nain",
    "Elfique",
    "Géant",
    "Gnomique",
    "Gobelin",
    "Halfelin",
    "Orc",
    "Abyssal",
    "Céleste",
    "Draconique",
    "Profond",
    "Infernal",
    "Primordial",
    "Sylvestre",
    "Sous-commun",
    "Langue des signes commune",
]

CLASS_RULES = {
    "Barbarian": {
        "hit_die": 12,
        "saving_throws": ["force", "constitution"],
        "proficiencies": {
            "armors": ["light", "medium", "shields"],
            "weapons": ["simple", "martial"],
        },
        "description": "Combattant sauvage et endurant, le barbare excelle en melee grace a sa rage et sa resistance.",
    },
    "Bard": {
        "hit_die": 8,
        "saving_throws": ["dexterite", "charisme"],
        "proficiencies": {
            "armors": ["light"],
            "weapons": ["simple"],
        },
        "description": "Artiste polyvalent, le barde soutient le groupe avec ses inspirations, sa magie et ses competences sociales.",
    },
    "Cleric": {
        "hit_die": 8,
        "saving_throws": ["sagesse", "charisme"],
        "proficiencies": {
            "armors": ["light", "medium", "shields"],
            "weapons": ["simple"],
        },
        "description": "Lanceur de sorts divin, le clerc soigne, protege ses allies et invoque la puissance de sa divinite.",
    },
    "Druid": {
        "hit_die": 8,
        "saving_throws": ["intelligence", "sagesse"],
        "proficiencies": {
            "armors": ["light", "medium", "shields"],
            "weapons": ["simple"],
        },
        "description": "Gardien de la nature, le druide maitrise les sorts elementaires et la metamorphose animale.",
    },
    "Fighter": {
        "hit_die": 10,
        "saving_throws": ["force", "constitution"],
        "proficiencies": {
            "armors": ["light", "medium", "heavy", "shields"],
            "weapons": ["simple", "martial"],
        },
        "description": "Specialiste des armes et armures, le guerrier est fiable en premiere ligne et tres adaptable.",
    },
    "Monk": {
        "hit_die": 8,
        "saving_throws": ["force", "dexterite"],
        "proficiencies": {
            "armors": [],
            "weapons": ["simple", "shortsword"],
        },
        "description": "Adepte du ki, le moine allie mobilite, precision et techniques martiales spectaculaires.",
    },
    "Paladin": {
        "hit_die": 10,
        "saving_throws": ["sagesse", "charisme"],
        "proficiencies": {
            "armors": ["light", "medium", "heavy", "shields"],
            "weapons": ["simple", "martial"],
        },
        "description": "Champion sacre, le paladin combine defense, soutien et gros degats grace a ses chatiments divins.",
    },
    "Ranger": {
        "hit_die": 10,
        "saving_throws": ["force", "dexterite"],
        "proficiencies": {
            "armors": ["light", "medium", "shields"],
            "weapons": ["simple", "martial"],
        },
        "description": "Eclaireur des terres sauvages, le rodeur piste ses proies et combat avec precision a distance ou au contact.",
    },
    "Rogue": {
        "hit_die": 8,
        "saving_throws": ["dexterite", "intelligence"],
        "proficiencies": {
            "armors": ["light"],
            "weapons": ["simple", "hand crossbow", "longsword", "rapier", "shortsword"],
        },
        "description": "Expert de l'infiltration, le roublard frappe juste au bon moment et excelle hors combat.",
    },
    "Sorcerer": {
        "hit_die": 6,
        "saving_throws": ["constitution", "charisme"],
        "proficiencies": {
            "armors": [],
            "weapons": ["simple"],
        },
        "description": "Magicien instinctif, l'ensorceleur puise sa puissance dans un heritage magique inne et modele ses sorts.",
    },
    "Warlock": {
        "hit_die": 8,
        "saving_throws": ["sagesse", "charisme"],
        "proficiencies": {
            "armors": ["light"],
            "weapons": ["simple"],
        },
        "description": "L'occultiste tire sa magie d'un pacte surnaturel, avec des pouvoirs atypiques et des invocations.",
    },
    "Wizard": {
        "hit_die": 6,
        "saving_throws": ["intelligence", "sagesse"],
        "proficiencies": {
            "armors": [],
            "weapons": ["simple"],
        },
        "description": "Erudit des arcanes, le magicien possede la plus large palette de sorts utilitaires et offensifs.",
    },
}

ABILITY_NAMES = ["force", "dexterite", "constitution", "intelligence", "sagesse", "charisme"]

BACKGROUND_RULES = {
    "Acolyte": {
        "skills": ["Insight", "Religion"],
        "tool": "Calligrapher’s Supplies",
        "origin_feat": "Magic Initiate (Cleric)",
        "feature": "Appel divin",
        "description": "Origine religieuse : vous etes forme aux rites et a l'etude du sacre.",
        "ability_options": ["intelligence", "sagesse", "charisme"],
    },
    "Artisan": {
        "skills": ["Investigation", "Persuasion"],
        "tool": "non spécifié",
        "origin_feat": "Crafter",
        "feature": "Savoir-faire",
        "description": "Vous venez d'un metier manuel ou d'atelier et savez valoriser votre expertise.",
        "ability_options": ["force", "dexterite", "intelligence"],
    },
    "Charlatan": {
        "skills": ["Deception", "Sleight of Hand"],
        "tool": "non spécifié",
        "origin_feat": "Skilled",
        "feature": "Arnaqueur de talent",
        "description": "Vous maitrisez les faux-semblants, les impostures et les manipulations sociales.",
        "ability_options": ["dexterite", "constitution", "charisme"],
    },
    "Criminal": {
        "skills": ["Sleight of Hand", "Stealth"],
        "tool": "non spécifié",
        "origin_feat": "Alert",
        "feature": "Réseau du milieu",
        "description": "Vous connaissez les codes des bas-fonds et savez operer discretement.",
        "ability_options": ["dexterite", "constitution", "intelligence"],
    },
    "Entertainer": {
        "skills": ["Acrobatics", "Performance"],
        "tool": "non spécifié",
        "origin_feat": "Musician",
        "feature": "Art de la scene",
        "description": "Vous savez captiver un public et faire de votre presence un atout.",
        "ability_options": ["force", "dexterite", "charisme"],
    },
    "Farmer": {
        "skills": ["Animal Handling", "Nature"],
        "tool": "non spécifié",
        "origin_feat": "Tough",
        "feature": "Vie rurale",
        "description": "Vous etes rompu aux travaux du quotidien et a la vie au grand air.",
        "ability_options": ["force", "constitution", "sagesse"],
    },
    "Guard": {
        "skills": ["Athletics", "Perception"],
        "tool": "non spécifié",
        "origin_feat": "Alert",
        "feature": "Vigilance",
        "description": "Vous etes habitue a proteger, patrouiller et reagir aux menaces.",
        "ability_options": ["force", "intelligence", "sagesse"],
    },
    "Guide": {
        "skills": ["Stealth", "Survival"],
        "tool": "non spécifié",
        "origin_feat": "Magic Initiate (Druid)",
        "feature": "Connaissance du terrain",
        "description": "Vous savez mener un groupe en milieu hostile et trouver votre route.",
        "ability_options": ["dexterite", "constitution", "sagesse"],
    },
    "Hermit": {
        "skills": ["Medicine", "Religion"],
        "tool": "non spécifié",
        "origin_feat": "Healer",
        "feature": "Recul et introspection",
        "description": "Votre retraite vous a apporte discipline, endurance et sagesse interieure.",
        "ability_options": ["constitution", "sagesse", "charisme"],
    },
    "Merchant": {
        "skills": ["Animal Handling", "Persuasion"],
        "tool": "non spécifié",
        "origin_feat": "Lucky",
        "feature": "Sens des affaires",
        "description": "Vous savez negocier, estimer et tirer profit des opportunites.",
        "ability_options": ["constitution", "intelligence", "charisme"],
    },
    "Noble": {
        "skills": ["History", "Persuasion"],
        "tool": "non spécifié",
        "origin_feat": "Skilled",
        "feature": "Etiquette de cour",
        "description": "Vous evoluez avec aisance dans les cercles d'influence et de pouvoir.",
        "ability_options": ["force", "intelligence", "charisme"],
    },
    "Sage": {
        "skills": ["Arcana", "History"],
        "tool": "non spécifié",
        "origin_feat": "Magic Initiate (Wizard)",
        "feature": "Erudition",
        "description": "Vous avez passe votre vie a compiler, etudier et transmettre le savoir.",
        "ability_options": ["constitution", "intelligence", "sagesse"],
    },
    "Sailor": {
        "skills": ["Perception", "Acrobatics"],
        "tool": "non spécifié",
        "origin_feat": "Tavern Brawler",
        "feature": "Marin aguerri",
        "description": "Vous connaissez les navires, les tempetes et la vie de pont.",
        "ability_options": ["force", "dexterite", "sagesse"],
    },
    "Scribe": {
        "skills": ["Investigation", "Perception"],
        "tool": "non spécifié",
        "origin_feat": "Skilled",
        "feature": "Memoire ecrite",
        "description": "Vous etes forme aux archives, aux manuscrits et aux details cruciaux.",
        "ability_options": ["dexterite", "intelligence", "sagesse"],
    },
    "Soldier": {
        "skills": ["Athletics", "Intimidation"],
        "tool": "non spécifié",
        "origin_feat": "Savage Attacker",
        "feature": "Formation militaire",
        "description": "Vous avez appris la discipline, la tactique et le travail d'unite.",
        "ability_options": ["force", "dexterite", "constitution"],
    },
    "Wayfarer": {
        "skills": ["Insight", "Stealth"],
        "tool": "Thieves’ Tools",
        "origin_feat": "Lucky",
        "feature": "Voyageur",
        "description": "Vous avez l'habitude de vivre sur les routes et d'improviser partout.",
        "ability_options": ["dexterite", "sagesse", "charisme"],
    },
}


def _translate_term(term):
    return TERM_TRANSLATIONS_FR.get(term, term)


def _translate_term_list(terms):
    return [_translate_term(term) for term in terms]


def get_localized_class_rules():
    localized_rules = {}
    for class_name, class_data in CLASS_RULES.items():
        localized_rules[class_name] = {
            **class_data,
            "proficiencies": {
                "armors": _translate_term_list(class_data.get("proficiencies", {}).get("armors", [])),
                "weapons": _translate_term_list(class_data.get("proficiencies", {}).get("weapons", [])),
            },
        }
    return localized_rules


def get_localized_species_rules():
    localized_rules = {}
    for species_name, species_data in SPECIES_RULES.items():
        localized_rules[species_name] = {
            **species_data,
            "traits": _translate_term_list(species_data.get("traits", [])),
            "proficiencies": _translate_term_list(species_data.get("proficiencies", [])),
        }
    return localized_rules


def get_localized_background_rules():
    localized_rules = {}
    for background_name, background_data in BACKGROUND_RULES.items():
        localized_rules[background_name] = {
            **background_data,
            "skills": _translate_term_list(background_data.get("skills", [])),
            "tool": _translate_term(background_data.get("tool", "")),
            "origin_feat": _translate_term(background_data.get("origin_feat", "")),
        }
    return localized_rules


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


def _resolve_base_scores(form_data):
    mode = (form_data.get("ability_mode") or "standard").lower()
    base_scores = {}
    for ability in ABILITY_NAMES:
        raw_value = form_data.get(f"{ability}_base", form_data.get(ability, 10))
        base_scores[ability] = _clamp(int(raw_value), 1, 20)

    values = list(base_scores.values())
    if mode == "standard":
        if sorted(values, reverse=True) != sorted(STANDARD_ARRAY, reverse=True):
            raise ValueError("Le mode standard doit utiliser exactement les valeurs 15, 14, 13, 12, 10, 8.")
    elif mode == "point_buy":
        if any(value not in POINT_BUY_COSTS for value in values):
            raise ValueError("Le mode Point Buy autorise uniquement des scores entre 8 et 15.")
        total_cost = sum(POINT_BUY_COSTS[value] for value in values)
        if total_cost > POINT_BUY_BUDGET:
            raise ValueError(f"Le mode Point Buy depasse le budget de {POINT_BUY_BUDGET} points.")
    return base_scores


def resolve_character_creation(form_data):
    """Calcule les stats finales et les valeurs dérivées selon les règles 2024."""
    level = _clamp(int(form_data.get("level", 1)), 1, 20)
    race = form_data.get("race", "Human")
    character_class = form_data.get("character_class", "Fighter")
    background_name = form_data.get("background_story", "Acolyte")

    base_scores = _resolve_base_scores(form_data)

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
