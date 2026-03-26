"""Chargement de la base de sorts DnD locale."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.utils.character_builder_engine import SpellResolverService, get_rules_loaders

CATALOG_PATH = Path(__file__).resolve().parents[2] / "app" / "data" / "spells_catalog.json"


def _normalize_spell_name(value: str) -> str:
    return (
        (value or "")
        .strip()
        .lower()
        .replace("’", "'")
        .replace("`", "'")
    )


def _build_spell_classes_from_rules_json() -> dict[str, set[str]]:
    loaders = get_rules_loaders()
    if not loaders.has_knowledge_base() or not loaders.spells_by_class_and_level:
        return {}

    spell_resolver = SpellResolverService(loaders)
    classes_by_spell: dict[str, set[str]] = {}

    for class_name, by_level in loaders.spells_by_class_and_level.items():
        canonical_class = spell_resolver.canonical_class(class_name)
        for spell_names in by_level.values():
            for spell_name in spell_names:
                classes_by_spell.setdefault(spell_name, set()).add(canonical_class)

    return classes_by_spell


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


def _load_spell_catalog_from_rules_json() -> list[dict[str, Any]]:
    loaders = get_rules_loaders()
    if not loaders.has_knowledge_base() or not loaders.spell_by_id:
        return []

    spell_resolver = SpellResolverService(loaders)
    class_spell_index = loaders.spells_by_class_and_level
    classes_by_spell = _build_spell_classes_from_rules_json()

    normalized: list[dict[str, Any]] = []
    for spell in loaders.spell_by_id.values():
        normalized_entry = _normalize_spell_entry(spell)
        spell_key = _normalize_spell_name(spell.get("name") or spell.get("name_fr") or spell.get("id") or "")
        extra_classes = classes_by_spell.get(spell_key, set())
        current_classes = {str(item).strip().lower() for item in normalized_entry.get("classes") or [] if str(item).strip()}
        normalized_entry["classes"] = sorted(current_classes | extra_classes)
        if normalized_entry["name"]:
            normalized.append(normalized_entry)

    # Tolérance haute : ajouter les sorts connus seulement via spells_by_class.json
    known_spell_names = {_normalize_spell_name(spell.get("name") or spell.get("name_en") or "") for spell in normalized}
    for class_name, by_level in class_spell_index.items():
        canonical_class = spell_resolver.canonical_class(class_name)
        for level, spell_names in by_level.items():
            for spell_name in spell_names:
                if spell_name in known_spell_names:
                    continue
                normalized.append({
                    "name": spell_name.title(),
                    "name_en": spell_name.title(),
                    "level": level,
                    "school": "",
                    "classes": [canonical_class],
                    "source": "",
                    "description": "",
                    "casting_time": "",
                    "range": "",
                    "duration": "",
                    "concentration": "Non",
                    "ritual": "Non",
                })
                known_spell_names.add(spell_name)

    return normalized


def load_spell_catalog() -> list[dict[str, Any]]:
    """Retourner la liste complete des sorts depuis la base JSON prioritaire, sinon fallback legacy."""
    rules_json_spells = _load_spell_catalog_from_rules_json()
    if rules_json_spells:
        return rules_json_spells

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
    classes_by_spell = _build_spell_classes_from_rules_json()

    for spell in spells:
        if not isinstance(spell, dict):
            continue
        normalized_spell = _normalize_spell_entry(spell)
        spell_key = _normalize_spell_name(spell.get("name") or spell.get("name_fr") or spell.get("id") or "")
        extra_classes = classes_by_spell.get(spell_key, set())
        current_classes = {str(item).strip().lower() for item in normalized_spell.get("classes") or [] if str(item).strip()}
        normalized_spell["classes"] = sorted(current_classes | extra_classes)
        if normalized_spell["name"]:
            normalized.append(normalized_spell)

    return normalized


def get_spells_for_level(level: int) -> list[dict[str, Any]]:
    """Filtrer les sorts sur un niveau précis."""
    return sorted(
        [spell for spell in load_spell_catalog() if spell.get("level") == level],
        key=lambda entry: entry.get("name", ""),
    )


def get_cantrips() -> list[dict[str, Any]]:
    """Alias de lisibilité pour les sorts mineurs (niveau 0)."""
    return get_spells_for_level(0)
