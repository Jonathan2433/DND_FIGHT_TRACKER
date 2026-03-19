"""Recupere les sorts mineurs depuis une API publique puis met a jour le catalogue local."""
from __future__ import annotations

import json
import ssl
import urllib.parse
import urllib.request
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parents[1] / "app" / "data" / "spells_catalog.json"
OPEN5E_URL = "https://api.open5e.com/v1/spells/"


def _fetch_json(url: str) -> dict:
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(url, context=ctx, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _fetch_open5e_cantrips() -> list[dict]:
    cantrips: list[dict] = []
    next_url = f"{OPEN5E_URL}?{urllib.parse.urlencode({'level_int': 0, 'limit': 200})}"

    while next_url:
        payload = _fetch_json(next_url)
        for raw_spell in payload.get("results", []):
            cantrips.append(
                {
                    "name": (raw_spell.get("name") or "").strip(),
                    "level": 0,
                    "school": (raw_spell.get("school") or "").strip(),
                    "classes": [item.strip() for item in (raw_spell.get("dnd_class") or "").split(",") if item.strip()],
                    "source": (raw_spell.get("document__title") or "Open5e").strip(),
                    "description": (raw_spell.get("desc") or "").strip(),
                }
            )
        next_url = payload.get("next")

    return sorted([spell for spell in cantrips if spell["name"]], key=lambda spell: spell["name"])


def _load_catalog() -> list[dict]:
    if not CATALOG_PATH.exists():
        return []
    with CATALOG_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict):
        return payload.get("spells") or []
    if isinstance(payload, list):
        return payload
    return []


def _write_catalog(spells: list[dict]) -> None:
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CATALOG_PATH.open("w", encoding="utf-8") as handle:
        json.dump({"spells": spells}, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> None:
    catalog = _load_catalog()
    remote_cantrips = _fetch_open5e_cantrips()

    non_cantrips = [spell for spell in catalog if int(spell.get("level", 0) or 0) != 0]
    merged = non_cantrips + remote_cantrips
    merged.sort(key=lambda spell: (int(spell.get("level", 0) or 0), spell.get("name", "")))

    _write_catalog(merged)
    print(f"Catalogue mis a jour: {len(merged)} sorts au total, dont {len(remote_cantrips)} sorts mineurs synchronises.")


if __name__ == "__main__":
    main()
