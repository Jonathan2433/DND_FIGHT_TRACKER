"""Constantes de l'application D&D Combat Tracker"""

# =====================
# TEMPLATES DE MONSTRES
# =====================

MONSTER_TEMPLATES = {
    "Gobelin": {
        "type": "Ennemi",
        "hp": 7,
        "ac": 15,
        "initiative": 2
    },
    "Hobgobelin": {
        "type": "Ennemi",
        "hp": 11,
        "ac": 18,
        "initiative": 1
    },
    "Bugbear": {
        "type": "Ennemi",
        "hp": 27,
        "ac": 16,
        "initiative": 2
    },
    "Redbrand Ruffian": {
        "type": "Ennemi",
        "hp": 11,
        "ac": 14,
        "initiative": 1
    },
    "Loup": {
        "type": "Ennemi",
        "hp": 11,
        "ac": 13,
        "initiative": 2
    },
    "Nothic": {
        "type": "Boss",
        "hp": 45,
        "ac": 15,
        "initiative": 3
    },
    "Spectre": {
        "type": "Ennemi",
        "hp": 22,
        "ac": 12,
        "initiative": 2
    },
    "Gelatinous Cube": {
        "type": "Ennemi",
        "hp": 84,
        "ac": 6,
        "initiative": -4
    },
    "Venomfang (Young Green Dragon)": {
        "type": "Boss",
        "hp": 136,
        "ac": 18,
        "initiative": 1
    }
}

# =====================
# CONDITIONS D&D 5E
# =====================

CONDITIONS_LIST = [
    "Aveuglé",
    "Charmé",
    "Assourdi",
    "Effrayé",
    "Agrippé",
    "Paralysé",
    "Pétrifié",
    "Empoisonné",
    "À terre",
    "Entravé",
    "Étourdi",
    "Inconscient",
    "Épuisement",
    "Concentration"
]

CONDITIONS_DESCRIPTIONS = {
    "Aveuglé": "Ne voit rien. Échoue automatiquement aux tests basés sur la vue. Attaques contre lui avec avantage ; ses attaques avec désavantage.",
    "Charmé": "Ne peut pas attaquer ou cibler le charmeur avec des effets nuisibles. Le charmeur a avantage aux tests sociaux contre lui.",
    "Assourdi": "N'entend rien. Échoue automatiquement aux tests basés sur l'ouïe.",
    "Effrayé": "Désavantage aux tests et attaques tant que la source est visible. Ne peut pas se rapprocher volontairement de la source.",
    "Agrippé": "Vitesse = 0. Fin si l'agrippeur est neutralisé ou éloigné.",
    "Paralysé": "Incapable d'agir. Échoue aux sauvegardes FOR/DEX. Attaques contre lui avec avantage. Coup critique automatique au contact.",
    "Pétrifié": "Transformé en pierre. Incapable d'agir. Résistance à tous les dégâts. Immunisé poison/maladie.",
    "Empoisonné": "Désavantage aux jets d'attaque et tests de caractéristique.",
    "À terre": "Désavantage aux attaques. Attaques contre lui avec avantage au corps à corps, désavantage à distance.",
    "Entravé": "Vitesse = 0. Désavantage aux attaques et sauvegardes DEX. Attaques contre lui avec avantage.",
    "Étourdi": "Incapable d'agir. Échoue aux sauvegardes FOR/DEX. Attaques contre lui avec avantage.",
    "Inconscient": "Incapable d'agir, tombe à terre. Échoue FOR/DEX. Attaques contre lui avec avantage. Critique auto au contact.",
    "Épuisement": "Applique des pénalités cumulatives selon le niveau d'épuisement.",
    "Concentration": "Si vous subissez des dégâts, vous devez réussir un jet de sauvegarde de Constitution pour maintenir le sort."
}

# =====================
# TYPES DE COMBATTANTS
# =====================

COMBATANT_TYPES = [
    "PJ",
    "Ennemi",
    "Boss",
    "Neutre"
]

# =====================
# UPLOAD ET FICHIERS
# =====================

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}

# =====================
# ACTIONS DE COMBAT
# =====================

COMBAT_ACTION_TYPES = [
    "damage",
    "heal",
    "condition",
    "ac_mod",
    "temp_hp",
    "status",
    "turn_time",
    "round_time"
]

# =====================
# DIFFICULTÉS DE RENCONTRES
# =====================

ENCOUNTER_DIFFICULTIES = [
    "Easy",
    "Medium",
    "Hard",
    "Deadly"
]