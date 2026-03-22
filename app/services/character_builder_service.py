"""Service central pour le funnel de creation de personnage pilote par JSON."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


class CharacterBuilderService:
    """Construit les payloads filtres pour chaque etape du builder."""

    def __init__(self, data_dir: Path | None = None):
        base_dir = data_dir or Path(__file__).resolve().parents[1] / "data" / "DND_RULES_JSON"
        self.data_dir = base_dir

        self.character_creation_rules = self._load_json("character_creation_rules.json", default={})
        self.class_catalog = self._load_json("class_catalog.json", default=[])
        self.class_choice_rules = self._load_json("class_choice_rules.json", default=[])
        self.backgrounds = self._load_json("backgrounds.json", default=[])
        self.species = self._load_json("species.json", default=[])
        self.species_choice_rules = self._load_json("species_choice_rules.json", default=[])
        self.starting_ability_score_methods = self._load_json("starting_ability_score_methods.json", default=[])
        self.spellcasting_rules = self._load_json("spellcasting_rules.json", default={})
        self.spells_by_class = self._load_json("spells_by_class.json", default={})
        self.spells = self._load_json("spells.json", default=[])
        self.subchoices_catalog = self._load_json("subchoices_catalog.json", default=[])
        self.equipment_items = self._load_json("equipment_items.json", default=[])
        self.equipment_items_adventuring_gear = self._load_json("equipment_items_adventuring_gear.json", default=[])
        self.starting_equipment_packs = self._load_json("starting_equipment_packs.json", default=[])
        self.weapons_catalog = self._load_json("weapons_catalog.json", default=[])
        self.tools = self._load_json("tools.json", default=[])
        self.skills = self._load_json("skills.json", default=[])
        self.languages = self._load_json("languages.json", default=[])
        self.origin_feats = self._load_json("origin_feats.json", default=[])
        self.feat_choices_rules = self._load_json("feat_choices_rules.json", default=[])
        self.class_features = self._load_json("class_features.json", default=[])
        self.fighting_styles = self._load_json("fighting_styles.json", default=[])
        self.eldritch_invocations = self._load_json("eldritch_invocations.json", default=[])
        self.weapon_masteries = self._load_json("weapon_masteries.json", default=[])
        self.equipment_choice_rules = self._load_json("equipment_choice_rules.json", default=[])

        self.class_by_id = self._index(self.class_catalog)
        self.background_by_id = self._index(self.backgrounds)
        self.species_by_id = self._index(self.species)
        self.skill_by_id = self._index(self.skills)
        self.tool_by_id = self._index(self.tools)
        self.language_by_id = self._index(self.languages)
        self.spell_by_id = self._index(self.spells)
        self.catalog_by_id = self._index(self.subchoices_catalog)
        self.origin_feat_by_id = self._index(self.origin_feats)
        self.feat_choice_by_id = {
            str(rule.get("feat_id")): rule
            for rule in self.feat_choices_rules
            if isinstance(rule, dict) and rule.get("feat_id")
        }

    def _load_json(self, filename: str, default: Any) -> Any:
        target = self.data_dir / filename
        if not target.exists():
            return default
        try:
            return json.loads(target.read_text(encoding="utf-8"))
        except Exception:
            return default

    @staticmethod
    def _index(items: Any) -> dict[str, dict[str, Any]]:
        if not isinstance(items, list):
            return {}
        return {str(i.get("id")): i for i in items if isinstance(i, dict) and i.get("id")}

    @staticmethod
    def _label(entry: dict[str, Any]) -> str:
        return (
            entry.get("name_fr")
            or entry.get("label_fr")
            or entry.get("name")
            or entry.get("name_en")
            or entry.get("label")
            or entry.get("id")
            or ""
        )

    def get_step_order(self) -> list[dict[str, Any]]:
        return self.character_creation_rules.get("step_order", []) if isinstance(self.character_creation_rules, dict) else []

    def get_available_classes(self) -> list[dict[str, Any]]:
        return [
            {
                "id": item["id"],
                "label": self._label(item),
                "description": item.get("description_fr") or item.get("description") or "",
            }
            for item in self.class_catalog
            if isinstance(item, dict)
        ]

    def get_available_backgrounds(self) -> list[dict[str, Any]]:
        return [{"id": item["id"], "label": self._label(item)} for item in self.backgrounds if isinstance(item, dict)]

    def get_available_species(self) -> list[dict[str, Any]]:
        return [{"id": item["id"], "label": self._label(item)} for item in self.species if isinstance(item, dict)]

    def _find_class_rule(self, class_id: str) -> dict[str, Any]:
        return next((rule for rule in self.class_choice_rules if isinstance(rule, dict) and rule.get("class_id") == class_id), {})

    def _find_species_rule(self, species_id: str) -> dict[str, Any]:
        return next((rule for rule in self.species_choice_rules if isinstance(rule, dict) and rule.get("species_id") == species_id), {})

    def _expand_ids(self, ids: list[str], source: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        resolved = []
        for item_id in ids:
            item = source.get(str(item_id))
            if item:
                resolved.append({"id": item_id, "label": self._label(item)})
            else:
                resolved.append({"id": item_id, "label": str(item_id)})
        return resolved

    @staticmethod
    def _dedupe_options(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for option in options:
            option_id = str(option.get("id", ""))
            if not option_id or option_id in seen:
                continue
            seen.add(option_id)
            deduped.append(option)
        return deduped

    def _resolve_subchoice_catalog(self, catalog_id: str, state: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        catalog = self.catalog_by_id.get(catalog_id, {})
        if not catalog:
            return []

        if catalog.get("choice_type") == "spell" and isinstance(catalog.get("resolver"), dict):
            resolver = catalog["resolver"]
            class_id = resolver.get("class_id") or (state or {}).get("class_id")
            spell_level = int(resolver.get("spell_level", 0))
            return self._resolve_spells_from_class(class_id, max_level=spell_level, exact_level=spell_level)

        return self._expand_ids(catalog.get("items", []), {
            **self.skill_by_id,
            **self.tool_by_id,
            **self.language_by_id,
            **self.spell_by_id,
        })

    def _resolve_feat_options(self, choice: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
        all_feats = [feat for feat in self.origin_feats if isinstance(feat, dict)]
        feat_filter = choice.get("filter", {}) if isinstance(choice.get("filter"), dict) else {}
        background_feat_id = (
            self.background_by_id.get(state.get("background_id") or "", {}).get("origin_feat", {}).get("id")
            if state.get("background_id")
            else None
        )
        selected_origin_feat = state.get("selected_origin_feat_id")

        options: list[dict[str, Any]] = []
        for feat in all_feats:
            feat_id = feat.get("id")
            if not feat_id:
                continue
            if feat_filter.get("feat_category") and feat.get("feat_category") != feat_filter.get("feat_category"):
                continue
            if feat_filter.get("available_at_character_level_1") and not feat.get("available_at_character_level_1"):
                continue
            if choice.get("exclude_if_already_owned") and feat_id in {background_feat_id, selected_origin_feat}:
                continue
            options.append(
                {
                    "id": feat_id,
                    "label": self._label(feat),
                    "feat_category": feat.get("feat_category", "origin"),
                }
            )
        return self._dedupe_options(options)

    def _resolve_spells_from_class(self, class_id: str | None, max_level: int = 1, exact_level: int | None = None) -> list[dict[str, Any]]:
        if not class_id:
            return []
        mapping = self.spells_by_class.get(class_id, {}) if isinstance(self.spells_by_class, dict) else {}
        names: set[str] = set()
        if isinstance(mapping, dict):
            for level_str, spell_names in mapping.items():
                try:
                    level = int(level_str)
                except Exception:
                    continue
                if exact_level is not None and level != exact_level:
                    continue
                if exact_level is None and level > max_level:
                    continue
                if isinstance(spell_names, list):
                    names.update(str(n) for n in spell_names)

        result = []
        normalized = {self._label(s).lower(): s for s in self.spells if isinstance(s, dict)}
        for name in sorted(names):
            spell = normalized.get(name.lower())
            if spell:
                result.append({"id": spell.get("id", name), "label": self._label(spell)})
            else:
                result.append({"id": name, "label": name})
        return result

    def _resolve_choice_options(self, choice: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
        if not isinstance(choice, dict):
            return []
        if isinstance(choice.get("options"), list):
            values = choice["options"]
            choice_type = choice.get("choice_type")
            index = {
                "skill_proficiency": self.skill_by_id,
                "tool_proficiency": self.tool_by_id,
                "language": self.language_by_id,
                "spell": self.spell_by_id,
                "fighting_style": self._index(self.fighting_styles),
            }.get(choice_type, {})
            options = self._expand_ids(values, index) if index else [{"id": x, "label": str(x)} for x in values]
            return self._dedupe_options(options)

        from_catalog = choice.get("from_catalog")
        if from_catalog:
            options = self._resolve_subchoice_catalog(from_catalog, state)
            restricted = set(choice.get("restricted_to", [])) if isinstance(choice.get("restricted_to"), list) else None
            if restricted:
                options = [opt for opt in options if opt.get("id") in restricted]
            return self._dedupe_options(options)

        from_catalogs = choice.get("from_catalogs")
        if isinstance(from_catalogs, list):
            merged: list[dict[str, Any]] = []
            for catalog_id in from_catalogs:
                merged.extend(self._resolve_subchoice_catalog(str(catalog_id), state))
            return self._dedupe_options(merged)

        from_spell_list = choice.get("from_spell_list")
        if isinstance(from_spell_list, dict):
            class_id = from_spell_list.get("class_id") or state.get("class_id")
            max_level = int(from_spell_list.get("max_spell_level", 1))
            include_cantrips = bool(from_spell_list.get("include_cantrips", False))
            exact_level = None if include_cantrips else 1
            return self._dedupe_options(self._resolve_spells_from_class(class_id, max_level=max_level, exact_level=exact_level))

        if choice.get("choice_type") == "origin_feat":
            return self._resolve_feat_options(choice, state)
        if choice.get("choice_type") == "fighting_style":
            style_type = choice.get("restricted_to_style_type")
            options = [
                {"id": style.get("id"), "label": self._label(style)}
                for style in self.fighting_styles
                if isinstance(style, dict) and style.get("id") and (not style_type or style.get("style_type") == style_type)
            ]
            return self._dedupe_options(options)
        if choice.get("choice_type") == "ability":
            return [{"id": ability, "label": ability} for ability in choice.get("options", []) if isinstance(ability, str)]
        if choice.get("choice_type") == "spell_list":
            return [{"id": spell_list, "label": spell_list} for spell_list in choice.get("options", []) if isinstance(spell_list, str)]
        return []

    def _find_feat_rule(self, feat_id: str | None) -> dict[str, Any]:
        if not feat_id:
            return {}
        return self.feat_choice_by_id.get(str(feat_id), {})

    def get_feat_payload(self, feat_id: str | None, state: dict[str, Any]) -> dict[str, Any]:
        feat = self.origin_feat_by_id.get(str(feat_id or ""), {})
        rule = self._find_feat_rule(feat_id)
        required_choices: list[dict[str, Any]] = []
        for choice in rule.get("choices", []) if isinstance(rule, dict) else []:
            if not isinstance(choice, dict):
                continue
            dynamic_from = choice.get("dynamic_from_previous_choice")
            dynamic_map = choice.get("catalog_map") if isinstance(choice.get("catalog_map"), dict) else {}
            options = self._resolve_choice_options(choice, state)
            if dynamic_from and dynamic_map and not options:
                dynamic_options: list[dict[str, Any]] = []
                for dynamic_key, catalog_id in dynamic_map.items():
                    for option in self._resolve_subchoice_catalog(str(catalog_id), state):
                        enriched = dict(option)
                        enriched["source_choice_value"] = dynamic_key
                        dynamic_options.append(enriched)
                options = self._dedupe_options(dynamic_options)
            required_choices.append(
                {
                    "id": choice.get("id"),
                    "type": choice.get("choice_type"),
                    "choose": int(choice.get("choose", 1)),
                    "required": bool(choice.get("required", True)),
                    "dynamic_from_previous_choice": dynamic_from,
                    "catalog_map": dynamic_map,
                    "options": options,
                }
            )
        return {
            "feat": feat,
            "feat_category": feat.get("feat_category") if isinstance(feat, dict) else None,
            "required_choices": required_choices,
        }

    def get_class_payload(self, class_id: str, state: dict[str, Any]) -> dict[str, Any]:
        class_data = self.class_by_id.get(class_id, {})
        class_rule = self._find_class_rule(class_id)
        automatic_gains = {
            "saving_throw_proficiencies": class_data.get("saving_throw_proficiencies", []),
            "weapon_proficiencies": class_data.get("weapon_proficiencies", []),
            "armor_training": class_data.get("armor_training", []),
            "features_level_1": class_data.get("level_1_features", []),
            "hit_die": class_data.get("hit_die"),
        }

        required = []
        for choice in class_rule.get("choices", []):
            if not isinstance(choice, dict):
                continue
            required.append(
                {
                    "id": choice.get("id"),
                    "type": choice.get("choice_type"),
                    "choose": int(choice.get("choose", 1)),
                    "required": bool(choice.get("required", True)),
                    "options": self._resolve_choice_options(choice, state),
                }
            )

        equipment = self._resolve_equipment_options(class_data.get("starting_equipment_options", []), state)
        return {
            "class": class_data,
            "automatic_gains": automatic_gains,
            "required_choices": required,
            "equipment_options": equipment,
        }

    def get_background_payload(self, background_id: str, state: dict[str, Any]) -> dict[str, Any]:
        bg = self.background_by_id.get(background_id, {})
        origin_feat = bg.get("origin_feat")
        origin_feat_id = origin_feat.get("id") if isinstance(origin_feat, dict) else None
        origin_feat_details = self.origin_feat_by_id.get(origin_feat_id, {}) if origin_feat_id else {}
        tool_prof = bg.get("tool_proficiency") if isinstance(bg, dict) else {}
        required_choices = []
        if isinstance(tool_prof, dict) and tool_prof.get("type") == "category_choice":
            options = self._resolve_subchoice_catalog(tool_prof.get("category", ""), state)
            required_choices.append(
                {
                    "id": f"{background_id}_tool_choice",
                    "type": "tool_proficiency",
                    "choose": int(tool_prof.get("choose", 1)),
                    "required": True,
                    "options": options,
                }
            )

        equipment = self._resolve_equipment_options(bg.get("starting_equipment_options", []), state)
        origin_feat_payload = self.get_feat_payload(origin_feat_id, state)
        return {
            "background": bg,
            "automatic_gains": {
                "skill_proficiencies": bg.get("skill_proficiencies", []),
                "tool_proficiency": bg.get("tool_proficiency"),
                "origin_feat": origin_feat,
            },
            "origin_feat_details": origin_feat_details,
            "origin_feat_payload": origin_feat_payload,
            "ability_score_options": bg.get("ability_score_options", {}),
            "required_choices": required_choices,
            "equipment_options": equipment,
        }

    def get_species_payload(self, species_id: str, state: dict[str, Any]) -> dict[str, Any]:
        species = self.species_by_id.get(species_id, {})
        species_rule = self._find_species_rule(species_id)
        required = []
        for choice in species_rule.get("choices", []):
            if not isinstance(choice, dict):
                continue
            options = self._resolve_choice_options(choice, state)
            if choice.get("choice_type") == "origin_feat":
                enriched_options = []
                for option in options:
                    option_id = option.get("id")
                    enriched = dict(option)
                    enriched["feat_payload"] = self.get_feat_payload(str(option_id), state)
                    enriched_options.append(enriched)
                options = enriched_options
            required.append(
                {
                    "id": choice.get("id"),
                    "type": choice.get("choice_type"),
                    "choose": int(choice.get("choose", 1)),
                    "required": bool(choice.get("required", True)),
                    "options": options,
                }
            )
        return {
            "species": species,
            "automatic_gains": {
                "traits_level_1": species.get("traits_level_1", []),
                "size_options": species.get("size_options", []),
                "speed": species.get("speed"),
            },
            "required_choices": required,
        }

    def get_language_payload(self, state: dict[str, Any]) -> dict[str, Any]:
        rules = self.character_creation_rules.get("languages", {}) if isinstance(self.character_creation_rules, dict) else {}
        defaults = rules.get("default_known_languages", ["common"])
        additional = rules.get("default_additional_language_choices", {})
        base_options = self._resolve_subchoice_catalog(additional.get("from", "standard_languages"), state)
        acquired = set(defaults)
        acquired.update(state.get("language_ids", []))
        filtered = [opt for opt in base_options if opt.get("id") not in acquired]
        return {
            "default_languages": defaults,
            "choose": int(additional.get("choose", 2)),
            "duplicates_not_allowed": bool(rules.get("duplicates_not_allowed", True)),
            "options": filtered,
        }

    def get_ability_score_payload(self, state: dict[str, Any]) -> dict[str, Any]:
        allowed_methods = [m for m in self.starting_ability_score_methods if isinstance(m, dict) and m.get("available_at_character_level_1")]
        background_id = state.get("background_id")
        background = self.background_by_id.get(background_id, {})
        return {
            "methods": [
                {
                    "id": method.get("id"),
                    "label": self._label(method),
                    "rules": method.get("rules", {}),
                    "recommended_default": bool(method.get("recommended_default")),
                }
                for method in allowed_methods
            ],
            "background_ability_score_options": background.get("ability_score_options", {}),
            "allowed_abilities": (background.get("ability_score_options", {}) or {}).get("allowed", []),
        }

    def _resolve_equipment_options(self, options: list[Any], state: dict[str, Any]) -> list[dict[str, Any]]:
        resolved = []
        for option in options or []:
            if not isinstance(option, dict):
                continue
            items = []
            for raw_item in option.get("items", []):
                if isinstance(raw_item, str):
                    item = self.equipment_by_id.get(raw_item) if hasattr(self, 'equipment_by_id') else None
                    if not item:
                        item = next((e for e in self.equipment_items if isinstance(e, dict) and e.get("id") == raw_item), None)
                    items.append({"type": "fixed", "id": raw_item, "label": self._label(item or {"id": raw_item})})
                elif isinstance(raw_item, dict) and raw_item.get("choice_from_category"):
                    choice_id = raw_item.get("choice_from_category")
                    items.append(
                        {
                            "type": "choice_from_category",
                            "id": raw_item.get("id") or choice_id,
                            "choose": int(raw_item.get("quantity", 1)),
                            "options": self._resolve_subchoice_catalog(choice_id, state),
                        }
                    )
            resolved.append({"id": option.get("id"), "label": option.get("label"), "items": items, "gold": option.get("gold", 0)})
        return resolved

    @property
    def equipment_by_id(self) -> dict[str, dict[str, Any]]:
        combined = [*self.equipment_items, *self.equipment_items_adventuring_gear, *self.starting_equipment_packs]
        return self._index(combined)


@lru_cache(maxsize=1)
def get_character_builder_service() -> CharacterBuilderService:
    return CharacterBuilderService()
