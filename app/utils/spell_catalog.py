"""Chargement de la base de sorts DnD locale."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CATALOG_PATH = Path(__file__).resolve().parents[2] / "app" / "data" / "spells_catalog.json"


def _normalize_spell_entry(raw_spell: dict[str, Any]) -> dict[str, Any]:
    """Normaliser un sort pour l'UI."""
    return {
        "name": (raw_spell.get("name") or "").strip(),
        "level": int(raw_spell.get("level", 0) or 0),
        "school": (raw_spell.get("school") or "").strip(),
        "classes": raw_spell.get("classes") or [],
        "source": (raw_spell.get("source") or "").strip(),
        "description": (raw_spell.get("description") or "").strip(),
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
