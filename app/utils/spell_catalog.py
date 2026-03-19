"""Chargement de la base de sorts DnD locale."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CATALOG_PATH = Path(__file__).resolve().parents[2] / "app" / "data" / "spells_catalog.json"


def _normalize_spell_entry(raw_spell: dict[str, Any]) -> dict[str, Any]:
    """Normaliser un sort pour l'UI."""
    raw_level = raw_spell.get("level", raw_spell.get("Lvl", 0))
    try:
        level = int(str(raw_level).strip() or 0)
    except (TypeError, ValueError):
        level = 0

    classes = raw_spell.get("classes")
    if not classes:
        classes = raw_spell.get("Classes")
    if isinstance(classes, str):
        classes = [item.strip() for item in classes.split(",") if item.strip()]
    elif not isinstance(classes, list):
        classes = []

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
        "name_en": str(raw_spell.get("name") or raw_spell.get("Spell") or "").strip(),
        "level": level,
        "school": str(raw_spell.get("school") or raw_spell.get("School") or "").strip(),
        "classes": classes,
        "source": str(raw_spell.get("source") or raw_spell.get("Source") or "").strip(),
        "description": str(description).strip(),
    }


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
