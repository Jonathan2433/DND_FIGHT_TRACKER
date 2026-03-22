"""Moteur de creation de personnage pilote par la base JSON DND_RULES_JSON."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    import jsonschema
except Exception:  # pragma: no cover - dependance optionnelle
    jsonschema = None


ABILITY_NAMES = ("force", "dexterite", "constitution", "intelligence", "sagesse", "charisme")
STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]
POINT_BUY_COSTS = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
POINT_BUY_BUDGET = 27


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower().replace("ô", "o").replace("é", "e").replace("è", "e")


def _normalize_spell_name(value: str | None) -> str:
    return _normalize(value).replace("’", "'").replace("`", "'")


class RulesLoaders:
    """Charge et indexe les catalogues/rules JSON."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.rules_dir = data_dir / "DND_RULES_JSON"

        self.class_catalog = self._load_json("class_catalog.json")
        self.class_features = self._load_json("class_features.json")
        self.backgrounds = self._load_json("backgrounds.json")
        self.species = self._load_json("species.json")
        self.species_choice_rules = self._load_json("species_choice_rules.json")
        self.origin_feats = self._load_json("origin_feats.json")
        self.feat_choices_rules = self._load_json("feat_choices_rules.json")
        self.skills = self._load_json("skills.json")
        self.languages = self._load_json("languages.json")
        self.proficiencies = self._load_json("proficiencies.json")
        self.equipment_items = self._load_json("equipment_items.json")
        self.equipment_items_adventuring_gear = self._load_json("equipment_items_adventuring_gear.json")
        self.starting_equipment_packs = self._load_json("starting_equipment_packs.json")
        self.spells = self._load_json("spells.json")
        self.spells_by_class = self._load_json("spells_by_class.json")
        self.spellcasting_rules = self._load_json("spellcasting_rules.json")
        self.class_choice_rules = self._load_json("class_choice_rules.json")
        self.character_creation_rules = self._load_json("character_creation_rules.json")
        self.character_schema = self._load_json("character_schema.json")
        self.builder_output_schema = self._load_json("builder_output_schema.json")

        self.class_by_id = self._build_index(self.class_catalog)
        self.background_by_id = self._build_index(self.backgrounds)
        self.species_by_id = self._build_index(self.species)
        self.feat_by_id = self._build_index(self.origin_feats)
        self.spell_by_id = self._build_index(self.spells)
        self.equipment_item_by_id = self._build_index(self.equipment_items)
        self.spells_by_class_and_level = self._build_spell_index_by_class_level()

    def has_knowledge_base(self) -> bool:
        return self.rules_dir.exists()

    def _load_json(self, filename: str) -> Any:
        path = self.rules_dir / filename
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception:
            return None

    @staticmethod
    def _build_index(payload: Any) -> dict[str, dict[str, Any]]:
        if not payload:
            return {}

        source = payload.get("items") if isinstance(payload, dict) else payload
        if not isinstance(source, list):
            return {}

        indexed: dict[str, dict[str, Any]] = {}
        for entry in source:
            if not isinstance(entry, dict):
                continue
            entry_id = str(entry.get("id") or entry.get("name") or "").strip()
            if not entry_id:
                continue
            indexed[entry_id] = entry
        return indexed

    def _build_spell_index_by_class_level(self) -> dict[str, dict[int, set[str]]]:
        index: dict[str, dict[int, set[str]]] = {}
        payload = self.spells_by_class
        if not payload:
            return index

        if isinstance(payload, dict):
            iterable = payload.items()
        else:
            iterable = []

        for class_id, raw_value in iterable:
            class_key = _normalize(class_id)
            if isinstance(raw_value, dict):
                level_map = raw_value
            elif isinstance(raw_value, list):
                level_map = {"0": [], "1": raw_value}
            else:
                continue

            for level_key, spell_list in level_map.items():
                try:
                    level = int(str(level_key).strip())
                except Exception:
                    continue
                if not isinstance(spell_list, list):
                    continue
                target = index.setdefault(class_key, {}).setdefault(level, set())
                for spell_name in spell_list:
                    normalized_name = _normalize_spell_name(str(spell_name))
                    if normalized_name:
                        target.add(normalized_name)
        return index


class SpellResolverService:
    """Resout les sorts en priorisant spells_by_class pour l'appartenance de classe."""

    CLASS_ALIASES = {
        "barde": "bard",
        "clerc": "cleric",
        "druide": "druid",
        "magicien": "wizard",
        "occultiste": "warlock",
        "rodeur": "ranger",
        "rôdeur": "ranger",
        "ensorceleur": "sorcerer",
        "barbare": "barbarian",
        "guerrier": "fighter",
        "roublard": "rogue",
        "moine": "monk",
        "artificier": "artificer",
    }

    def __init__(self, loaders: RulesLoaders):
        self.loaders = loaders

    def canonical_class(self, class_name: str | None) -> str:
        normalized = _normalize(class_name)
        return self.CLASS_ALIASES.get(normalized, normalized)

    def get_spells_for_class_level(self, class_name: str | None, level: int) -> list[dict[str, Any]]:
        class_key = self.canonical_class(class_name)
        by_class = self.loaders.spells_by_class_and_level.get(class_key, {})
        names = by_class.get(level, set())
        if not names:
            return []

        catalog = self.loaders.spell_by_id
        resolved: list[dict[str, Any]] = []

        for normalized_name in sorted(names):
            detail = self._find_spell_detail(catalog, normalized_name)
            if detail:
                resolved.append(detail)
            else:
                resolved.append(
                    {
                        "id": normalized_name,
                        "name": normalized_name.title(),
                        "level": level,
                        "school": "",
                        "description": "",
                        "classes": [class_key],
                    }
                )
        return resolved

    def _find_spell_detail(self, catalog: dict[str, dict[str, Any]], normalized_name: str) -> dict[str, Any] | None:
        for spell in catalog.values():
            name_candidates = {
                _normalize_spell_name(str(spell.get("name") or "")),
                _normalize_spell_name(str(spell.get("name_fr") or "")),
                _normalize_spell_name(str(spell.get("id") or "")),
            }
            if normalized_name in name_candidates:
                enriched = dict(spell)
                classes = enriched.get("available_to", {}).get("classes") if isinstance(enriched.get("available_to"), dict) else enriched.get("classes")
                if isinstance(classes, list):
                    enriched["classes"] = sorted({_normalize(c) for c in classes if _normalize(c)})
                return enriched
        return None


class CharacterBuilderService:
    """Assemble un personnage niveau 1+ selon l'orchestration JSON."""

    def __init__(self, loaders: RulesLoaders):
        self.loaders = loaders

    @staticmethod
    def _clamp(value: int, minimum: int, maximum: int) -> int:
        return max(minimum, min(maximum, value))

    @staticmethod
    def _ability_modifier(score: int) -> int:
        return (score - 10) // 2

    def resolve_base_scores(self, form_data) -> dict[str, int]:
        mode = (form_data.get("ability_mode") or "standard").lower()
        base_scores: dict[str, int] = {}
        for ability in ABILITY_NAMES:
            raw_value = form_data.get(f"{ability}_base", form_data.get(ability, 10))
            base_scores[ability] = self._clamp(int(raw_value), 1, 20)

        values = list(base_scores.values())
        if mode == "standard" and sorted(values, reverse=True) != sorted(STANDARD_ARRAY, reverse=True):
            raise ValueError("Le mode standard doit utiliser exactement les valeurs 15, 14, 13, 12, 10, 8.")
        if mode == "point_buy":
            if any(value not in POINT_BUY_COSTS for value in values):
                raise ValueError("Le mode Point Buy autorise uniquement des scores entre 8 et 15.")
            total_cost = sum(POINT_BUY_COSTS[value] for value in values)
            if total_cost > POINT_BUY_BUDGET:
                raise ValueError(f"Le mode Point Buy depasse le budget de {POINT_BUY_BUDGET} points.")
        return base_scores

    def resolve_background_bonuses(self, form_data, background_name: str) -> dict[str, int]:
        background = self.loaders.background_by_id.get(background_name, {})
        allowed = set(background.get("ability_options", [])) if isinstance(background, dict) else set()

        if not allowed and isinstance(background, dict):
            bonuses = background.get("ability_bonuses")
            if isinstance(bonuses, dict):
                for k, v in bonuses.items():
                    if v:
                        allowed.add(k)

        requested_bonus: dict[str, int] = {}
        for ability in ABILITY_NAMES:
            raw_value = form_data.get(f"{ability}_bg_bonus", 0)
            requested_bonus[ability] = self._clamp(int(raw_value), 0, 2) if ability in allowed else 0

        spent = sum(requested_bonus.values())
        if spent == 0 and allowed:
            for ability in allowed:
                requested_bonus[ability] = 1
            spent = sum(requested_bonus.values())

        if spent > 3:
            overflow = spent - 3
            for ability in ABILITY_NAMES:
                if overflow <= 0:
                    break
                reducible = min(overflow, requested_bonus[ability])
                requested_bonus[ability] -= reducible
                overflow -= reducible

        return requested_bonus

    def build_character(self, form_data) -> dict[str, Any]:
        level = self._clamp(int(form_data.get("level", 1)), 1, 20)
        species_name = form_data.get("race", "Human")
        class_name = form_data.get("character_class", "Fighter")
        background_name = form_data.get("background_choice") or form_data.get("background_story") or "Acolyte"

        base_scores = self.resolve_base_scores(form_data)
        background_bonus = self.resolve_background_bonuses(form_data, background_name)
        final_scores = {
            ability: self._clamp(base_scores[ability] + background_bonus.get(ability, 0), 1, 20)
            for ability in ABILITY_NAMES
        }

        class_rule = self.loaders.class_by_id.get(class_name, {})
        hit_die = int(class_rule.get("hit_die", 8) or 8)
        saving_throws = set(class_rule.get("saving_throws", []))

        constitution_mod = self._ability_modifier(final_scores["constitution"])
        average_gain = (hit_die // 2) + 1
        hp_max = max(1, hit_die + constitution_mod + (level - 1) * (average_gain + constitution_mod))

        dex_modifier = self._ability_modifier(final_scores["dexterite"])
        ac_base = int(form_data.get("ac_base", max(10, 10 + dex_modifier)))

        payload: dict[str, Any] = {
            "race": species_name,
            "character_class": class_name,
            "level": level,
            "hp_max": hp_max,
            "ac_base": ac_base,
            "initiative_bonus": dex_modifier,
        }
        payload.update(final_scores)

        for ability in ABILITY_NAMES:
            payload[f"maitrise_{ability}"] = ability in saving_throws

        return payload


class ValidationService:
    """Valide la sortie du builder contre les schemas si disponibles."""

    def __init__(self, loaders: RulesLoaders):
        self.loaders = loaders

    def validate(self, payload: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if not jsonschema:
            return errors

        for schema in (self.loaders.character_schema, self.loaders.builder_output_schema):
            if not isinstance(schema, dict):
                continue
            try:
                jsonschema.validate(payload, schema)
            except Exception as exc:
                errors.append(str(exc))
        return errors


@lru_cache(maxsize=1)
def get_rules_loaders() -> RulesLoaders:
    data_dir = Path(__file__).resolve().parents[2] / "app" / "data"
    return RulesLoaders(data_dir)
