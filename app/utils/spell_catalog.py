"""Chargement de la base de sorts DnD locale."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CATALOG_PATH = Path(__file__).resolve().parents[2] / "app" / "data" / "spells_catalog.json"


CLASS_SPELLS_LEVEL_0_1 = {
    "bard": {
        "Dancing Lights", "Message", "Mending", "Minor Illusion", "Prestidigitation", "Starry Wisp",
        "Thunderclap", "True Strike", "Vicious Mockery",
        "Animal Friendship", "Bane", "Charm Person", "Color Spray",
        "Command", "Cure Wounds", "Detect Magic", "Detect Thoughts", "Disguise Self", "Dissonant Whispers",
        "Faerie Fire", "Feather Fall", "Healing Word", "Heroism", "Identify", "Illusory Script",
        "Longstrider", "Silent Image", "Sleep", "Speak with Animals",
        "Tasha’s Hideous Laughter", "Thunderwave", "Unseen Servant",
    },
    "cleric": {
        "Guidance", "Light", "Mending", "Resistance", "Sacred Flame", "Spare the Dying", "Thaumaturgy",
        "Bane", "Bless", "Command", "Create or Destroy Water", "Cure Wounds", "Detect Evil and Good",
        "Detect Magic", "Detect Poison and Disease", "Guiding Bolt", "Healing Word", "Inflict Wounds",
        "Protection from Evil and Good", "Purify Food and Drink", "Sanctuary", "Shield of Faith",
    },
    "druid": {
        "Druidcraft", "Elementalism", "Guidance", "Mending", "Poison Spray", "Produce Flame", "Resistance",
        "Shillelagh", "Spare the Dying", "Starry Wisp",
        "Animal Friendship", "Animal Messenger", "Charm Person", "Create or Destroy Water", "Cure Wounds",
        "Detect Magic", "Detect Poison and Disease", "Entangle", "Faerie Fire", "Fog Cloud", "Goodberry",
        "Healing Word", "Ice Knife", "Jump", "Longstrider", "Purify Food and Drink",
        "Thunderwave",
    },
    "paladin": {
        "Bless", "Command", "Cure Wounds", "Detect Evil and Good", "Detect Magic", "Detect Poison and Disease",
        "Divine Favor", "Heroism", "Protection from Evil and Good", "Purify Food and Drink",
        "Searing Smite", "Shield of Faith",
    },
    "ranger": {
        "Alarm", "Animal Friendship", "Animal Messenger", "Cure Wounds", "Detect Magic",
        "Detect Poison and Disease", "Ensnaring Strike", "Entangle", "Fog Cloud", "Hunter’s Mark", "Jump",
        "Longstrider", "Speak with Animals",
    },
    "sorcerer": {
        "Acid Splash", "Chill Touch", "Dancing Lights", "Elementalism", "Fire Bolt", "Light", "Mage Hand",
        "Mending", "Message", "Mind Spike", "Minor Illusion", "Poison Spray", "Prestidigitation",
        "Ray of Frost", "Shocking Grasp", "Sorcerous Burst", "True Strike",
        "Burning Hands", "Charm Person", "Chromatic Orb", "Color Spray", "Detect Magic", "Disguise Self",
        "Expeditious Retreat", "False Life", "Feather Fall", "Fog Cloud", "Ice Knife", "Jump",
        "Mage Armor", "Magic Missile", "Ray of Sickness", "Shield", "Sleep", "Thunderwave",
    },
    "warlock": {
        "Chill Touch", "Eldritch Blast", "Mage Hand", "Mind Spike", "Minor Illusion", "Poison Spray",
        "Prestidigitation", "True Strike",
        "Bane", "Charm Person", "Comprehend Languages", "Detect Magic", "Expeditious Retreat",
        "Hellish Rebuke", "Hex", "Illusory Script", "Protection from Evil and Good",
        "Speak with Animals", "Tasha’s Hideous Laughter", "Unseen Servant",
    },
    "wizard": {
        "Acid Splash", "Chill Touch", "Dancing Lights", "Elementalism", "Fire Bolt", "Guidance", "Light",
        "Mage Hand", "Mending", "Message", "Mind Spike", "Minor Illusion", "Poison Spray",
        "Prestidigitation", "Ray of Frost", "Shocking Grasp", "True Strike",
        "Alarm", "Burning Hands", "Charm Person", "Chromatic Orb", "Color Spray", "Comprehend Languages",
        "Detect Magic", "Disguise Self", "Expeditious Retreat", "False Life", "Feather Fall", "Find Familiar",
        "Fog Cloud", "Grease", "Ice Knife", "Identify", "Illusory Script", "Jump",
        "Mage Armor", "Magic Missile", "Protection from Evil and Good", "Ray of Sickness", "Shield", "Sleep",
        "Tasha’s Hideous Laughter", "Thunderwave", "Unseen Servant",
    },
}


def _normalize_spell_name(value: str) -> str:
    return (
        (value or "")
        .strip()
        .lower()
        .replace("’", "'")
        .replace("`", "'")
    )


def _build_spell_class_overrides() -> dict[str, set[str]]:
    overrides: dict[str, set[str]] = {}
    for class_name, spell_names in CLASS_SPELLS_LEVEL_0_1.items():
        for spell_name in spell_names:
            key = _normalize_spell_name(spell_name)
            overrides.setdefault(key, set()).add(class_name)
    return overrides


SPELL_CLASS_OVERRIDES = _build_spell_class_overrides()


def _normalize_spell_entry(raw_spell: dict[str, Any]) -> dict[str, Any]:
    """Normaliser un sort pour l'UI."""
    raw_level = raw_spell.get("level", raw_spell.get("Lvl", 0))
    try:
        level = int(str(raw_level).strip() or 0)
    except (TypeError, ValueError):
        level = 0

    english_name = str(raw_spell.get("name") or raw_spell.get("Spell") or "").strip()
    french_name = str(raw_spell.get("name_fr") or raw_spell.get("Spell_FR") or "").strip()

    classes = raw_spell.get("classes")
    if not classes:
        classes = raw_spell.get("Classes")
    if isinstance(classes, str):
        classes = [item.strip() for item in classes.split(",") if item.strip()]
    elif not isinstance(classes, list):
        classes = []
    normalized_classes = {
        str(item).strip().lower()
        for item in classes
        if str(item).strip()
    }

    override_classes = (
        SPELL_CLASS_OVERRIDES.get(_normalize_spell_name(english_name))
        or SPELL_CLASS_OVERRIDES.get(_normalize_spell_name(french_name))
    )
    if override_classes:
        normalized_classes = set(override_classes)
    classes = sorted(normalized_classes)

    description = (
        raw_spell.get("description")
        or raw_spell.get("Description_FR")
        or raw_spell.get("Description")
        or ""
    )

    display_name = (
        raw_spell.get("name_fr")
        or raw_spell.get("Spell_FR")
        or raw_spell.get("name")
        or raw_spell.get("Spell")
        or ""
    )

    return {
        "name": str(display_name).strip(),
        "name_en": english_name,
        "level": level,
        "school": _translate_school(str(raw_spell.get("school") or raw_spell.get("School") or "").strip()),
        "classes": classes,
        "source": str(raw_spell.get("source") or raw_spell.get("Source") or "").strip(),
        "description": str(description).strip(),
        "casting_time": _translate_casting_time(str(raw_spell.get("casting_time") or raw_spell.get("Casting Time") or "").strip()),
        "range": _translate_range(str(raw_spell.get("range") or raw_spell.get("Range") or "").strip()),
        "duration": _translate_duration(str(raw_spell.get("duration") or raw_spell.get("Duration") or "").strip()),
        "concentration": _normalize_boolean_label(raw_spell.get("concentration") or raw_spell.get("Concentration")),
        "ritual": _normalize_boolean_label(raw_spell.get("ritual") or raw_spell.get("Ritual")),
    }


def _normalize_boolean_label(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"oui", "yes", "y", "true", "1"}:
        return "Oui"
    if not normalized:
        return "Non"
    return "Oui"


def _translate_school(school: str) -> str:
    labels = {
        "abjuration": "Abjuration",
        "conjuration": "Conjuration",
        "divination": "Divination",
        "enchantment": "Enchantement",
        "evocation": "Évocation",
        "illusion": "Illusion",
        "necromancy": "Nécromancie",
        "transmutation": "Transmutation",
    }
    key = school.strip().lower()
    return labels.get(key, school)


def _translate_casting_time(value: str) -> str:
    translated = value.strip()
    translated = re.sub(r"\b[Bb]onus [Aa]ction\b", "__BONUS_ACTION__", translated)
    translated = re.sub(r"\b[Rr]eaction\b", "1 réaction", translated)
    translated = re.sub(r"\b[Aa]ction\b", "1 action", translated)
    translated = translated.replace("__BONUS_ACTION__", "1 action bonus")
    translated = re.sub(r"\b[Rr]itual\b", "Rituel", translated)
    translated = re.sub(r"\bor\b", "ou", translated)
    return translated


def _translate_range(value: str) -> str:
    translated = value.replace("Self", "Personnel").replace("Touch", "Contact")
    translated = translated.replace("Unlimited", "Illimitée")
    translated = translated.replace(" ft", " pieds")
    return translated


def _translate_duration(value: str) -> str:
    translated = value
    mapping = {
        "Instantaneous": "Instantané",
        "Until dispelled": "Jusqu'à dissipation",
        "Special": "Spéciale",
        "Round": "round",
        "rounds": "rounds",
        "minute": "minute",
        "minutes": "minutes",
        "hour": "heure",
        "hours": "heures",
        "day": "jour",
        "days": "jours",
    }
    for english, french in mapping.items():
        translated = translated.replace(english, french)
    return translated


def load_spell_catalog() -> list[dict[str, Any]]:
    """Retourner la liste complete des sorts depuis le JSON local."""
    if not CATALOG_PATH.exists():
        return []

    with CATALOG_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, dict):
        spells = payload.get("spells") or []
    elif isinstance(payload, list):
        spells = payload
    else:
        spells = []

    normalized = []
    for spell in spells:
        if not isinstance(spell, dict):
            continue
        normalized_spell = _normalize_spell_entry(spell)
        if normalized_spell["name"]:
            normalized.append(normalized_spell)

    return normalized


def get_spells_for_level(level: int) -> list[dict[str, Any]]:
    """Filtrer les sorts sur un niveau precis."""
    return sorted(
        [spell for spell in load_spell_catalog() if spell.get("level") == level],
        key=lambda entry: entry.get("name", ""),
    )


def get_cantrips() -> list[dict[str, Any]]:
    """Alias de lisibilite pour les sorts mineurs (niveau 0)."""
    return get_spells_for_level(0)
