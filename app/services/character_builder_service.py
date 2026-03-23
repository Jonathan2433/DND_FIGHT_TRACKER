"""Service central pour le funnel de creation de personnage pilote par JSON."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


BUILDER_STATE_DEFAULTS: dict[str, Any] = {
    "class_id": None,
    "background_id": None,
    "species_id": None,
    "ability_score_method": None,
    "base_ability_scores": {},
    "background_ability_bonus_mode": None,
    "background_ability_bonus_allocations": [],
    "language_ids": [],
    "selected_class_choice_ids": [],
    "selected_species_choice_ids": [],
    "selected_feat_choice_ids": [],
    "selected_origin_feat_id": None,
    "selected_feat_ids": [],
    "selected_spell_ids_by_choice": {},
    "selected_equipment_choices_by_slot": {},
    "selected_equipment_ids": [],
    "selected_ability_bonus_ids": [],
}

BUILDER_STATE_ALIASES: dict[str, str] = {
    "ability_method_id": "ability_score_method",
    "ability_method": "ability_score_method",
    "base_abilities": "base_ability_scores",
    "base_abilities_json": "base_ability_scores",
    "ability_scores": "base_ability_scores",
    "selected_language_ids": "language_ids",
    "languages": "language_ids",
    "selected_class_choices": "selected_class_choice_ids",
    "class_choice_ids": "selected_class_choice_ids",
    "selected_species_choices": "selected_species_choice_ids",
    "species_choice_ids": "selected_species_choice_ids",
    "selected_feat_choices": "selected_feat_choice_ids",
    "feat_choice_ids": "selected_feat_choice_ids",
    "selected_spells_by_choice": "selected_spell_ids_by_choice",
    "equipment_choices_by_slot": "selected_equipment_choices_by_slot",
}

STEP_COMPONENT_IDS = {
    "choose_class",
    "choose_background",
    "choose_species",
    "choose_languages",
    "assign_ability_scores",
    "choose_equipment",
    "finalize",
}


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
        raw_spells_by_class = self._load_json("spells_by_class.json", default={})
        self.spells_by_class = self._normalize_spells_by_class(raw_spells_by_class)
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
        self.equipment_choice_rule_by_id = {
            str(rule.get("id")): rule
            for rule in self.equipment_choice_rules
            if isinstance(rule, dict) and rule.get("id")
        }

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
        self.class_feature_by_id = self._index(self.class_features)

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
    def _normalize_spells_by_class(raw_mapping: Any) -> dict[str, dict[str, Any]]:
        if isinstance(raw_mapping, dict):
            return raw_mapping
        if not isinstance(raw_mapping, list):
            return {}
        normalized: dict[str, dict[str, Any]] = {}
        for entry in raw_mapping:
            if not isinstance(entry, dict):
                continue
            class_id = str(entry.get("class_id") or "").strip()
            levels = entry.get("levels")
            if not class_id or not isinstance(levels, dict):
                continue
            normalized[class_id] = levels
        return normalized

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

    @staticmethod
    def _normalize_step_id(step_id: str) -> str:
        aliases = {
            "determine_ability_scores": "assign_ability_scores",
            "finalize_character": "finalize",
        }
        return aliases.get(step_id, step_id)

    def _extract_step_definitions(self, step: dict[str, Any], definitions: list[dict[str, Any]]) -> None:
        step_id = str(step.get("id") or step.get("step_id") or step.get("name") or "").strip()
        if not step_id:
            return

        normalized_id = self._normalize_step_id(step_id)
        substeps = step.get("substeps") if isinstance(step.get("substeps"), list) else []

        if substeps and normalized_id not in STEP_COMPONENT_IDS:
            for substep in substeps:
                if isinstance(substep, dict):
                    self._extract_step_definitions(substep, definitions)
            return

        if normalized_id not in STEP_COMPONENT_IDS:
            return

        definitions.append(
            {
                "id": normalized_id,
                "label": step.get("label_fr")
                or step.get("title_fr")
                or step.get("name_fr")
                or step.get("label")
                or step.get("title")
                or step.get("name_en")
                or normalized_id,
            }
        )

    def get_step_definitions(self) -> list[dict[str, Any]]:
        configured_steps = self.get_step_order()
        if isinstance(configured_steps, list) and configured_steps:
            definitions: list[dict[str, Any]] = []
            for raw_step in configured_steps:
                if isinstance(raw_step, dict):
                    self._extract_step_definitions(raw_step, definitions)
                elif isinstance(raw_step, str) and raw_step.strip():
                    step_id = self._normalize_step_id(raw_step.strip())
                    if step_id not in STEP_COMPONENT_IDS:
                        continue
                    definitions.append({"id": step_id, "label": step_id})
            if definitions:
                return definitions
        return [
            {"id": "choose_class", "label": "Classe"},
            {"id": "choose_background", "label": "Background"},
            {"id": "choose_species", "label": "Espèce"},
            {"id": "choose_languages", "label": "Langues"},
            {"id": "assign_ability_scores", "label": "Caractéristiques"},
            {"id": "choose_equipment", "label": "Équipement"},
            {"id": "finalize", "label": "Résumé"},
        ]

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

    def _build_auto_granted_summary(self, automatic_gains: dict[str, Any]) -> list[dict[str, Any]]:
        if not isinstance(automatic_gains, dict):
            return []
        label_by_key = {
            "saving_throw_proficiencies": "Jets de sauvegarde",
            "weapon_proficiencies": "Armes",
            "armor_training": "Armures",
            "features_level_1_details": "Capacités de niveau 1",
            "features_level_1": "Capacités de niveau 1",
            "hit_die": "Dé de vie",
            "skill_proficiencies": "Compétences",
            "tool_proficiency": "Outils",
            "origin_feat": "Don d'origine",
            "traits_level_1": "Traits de niveau 1",
            "size_options": "Tailles",
            "speed": "Vitesse",
        }
        summary: list[dict[str, Any]] = []
        for key, raw_value in automatic_gains.items():
            value = raw_value
            if isinstance(raw_value, list):
                if not raw_value:
                    continue
                value = [self._label(item) if isinstance(item, dict) else str(item) for item in raw_value]
            elif isinstance(raw_value, dict):
                if not raw_value:
                    continue
                if "id" in raw_value or "name_fr" in raw_value or "name" in raw_value:
                    value = self._label(raw_value)
                else:
                    value = ", ".join(
                        f"{nested_key}: {nested_value}" for nested_key, nested_value in raw_value.items() if nested_value not in (None, "", [])
                    )
            elif raw_value in (None, "", []):
                continue
            summary.append({"label": label_by_key.get(key, key), "value": value})
        return summary

    def _build_required_choices_summary(self, required_choices: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not isinstance(required_choices, list):
            return []
        type_labels = {
            "skill_proficiency": "Compétence",
            "tool_proficiency": "Outil",
            "language": "Langue",
            "spell": "Sort",
            "prepared_spell": "Sort préparé",
            "spellbook_entry": "Sort",
            "origin_feat": "Don",
            "size_choice": "Taille",
            "ability_bonus": "Bonus de caractéristique",
            "equipment": "Équipement",
        }
        summary: list[dict[str, Any]] = []
        for choice in required_choices:
            if not isinstance(choice, dict):
                continue
            options = choice.get("options", [])
            rendered_options = [
                self._label(option) if isinstance(option, dict) else str(option)
                for option in options
            ]
            summary.append(
                {
                    "id": choice.get("id"),
                    "label": type_labels.get(str(choice.get("type")), str(choice.get("type") or "choix")),
                    "choose": int(choice.get("choose", 1)),
                    "required": bool(choice.get("required", True)),
                    "options_count": len(options) if isinstance(options, list) else 0,
                    "options_preview": rendered_options[:6],
                }
            )
        return summary

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
        normalized: dict[str, dict[str, Any]] = {}
        for spell in self.spells:
            if not isinstance(spell, dict):
                continue
            for key in (
                spell.get("id"),
                spell.get("name"),
                spell.get("name_en"),
                spell.get("name_fr"),
                self._label(spell),
            ):
                normalized_key = str(key or "").strip().lower()
                if normalized_key:
                    normalized[normalized_key] = spell

        for name in sorted(names):
            lookup_key = str(name or "").strip().lower()
            spell = self.spell_by_id.get(str(name)) or normalized.get(lookup_key)
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
            option_labels = choice.get("option_labels")
            if isinstance(option_labels, dict):
                for option in options:
                    option_id = str(option.get("id", ""))
                    translated_label = option_labels.get(option_id)
                    if translated_label:
                        option["label_fr"] = str(translated_label)
                        option["display_label"] = str(translated_label)
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

        from_resolver = str(choice.get("from_resolver") or "")
        if from_resolver == "weapons_with_which_you_have_proficiency":
            class_id = str(state.get("class_id") or "")
            return self._resolve_weapons_with_class_proficiency(class_id)
        if from_resolver == "current_skill_proficiencies_only":
            current_skills = self._collect_current_skill_proficiencies(state)
            return self._expand_ids(sorted(current_skills), self.skill_by_id)
        if from_resolver == "wizard_spellbook_entries_only":
            class_id = str(state.get("class_id") or "")
            max_level = int(choice.get("spell_level_max", 1))
            return self._dedupe_options(self._resolve_spells_from_class(class_id, max_level=max_level, exact_level=max_level))

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
        if choice.get("choice_type") == "eldritch_invocation":
            max_level = int((choice.get("filter") or {}).get("available_at_level_lte", 1))
            options = [
                {"id": invocation.get("id"), "label": self._label(invocation)}
                for invocation in self.eldritch_invocations
                if isinstance(invocation, dict)
                and invocation.get("id")
                and int(invocation.get("available_at_level", 1) or 1) <= max_level
            ]
            return self._dedupe_options(options)
        if choice.get("choice_type") == "ability":
            return [{"id": ability, "label": ability} for ability in choice.get("options", []) if isinstance(ability, str)]
        if choice.get("choice_type") == "spell_list":
            return [{"id": spell_list, "label": spell_list} for spell_list in choice.get("options", []) if isinstance(spell_list, str)]
        return []

    def _resolve_weapons_with_class_proficiency(self, class_id: str) -> list[dict[str, Any]]:
        class_data = self.class_by_id.get(class_id, {})
        proficiencies = {str(entry) for entry in class_data.get("weapon_proficiencies", []) if entry}
        options: list[dict[str, Any]] = []
        for weapon in self.weapons_catalog:
            if not isinstance(weapon, dict) or not weapon.get("id"):
                continue
            weapon_category = str(weapon.get("weapon_category") or "")
            weapon_properties = {str(prop) for prop in weapon.get("properties", []) if prop}
            is_simple = weapon_category.startswith("simple_")
            is_martial = weapon_category.startswith("martial_")

            if "simple_weapons" in proficiencies and is_simple:
                options.append({"id": weapon["id"], "label": self._label(weapon)})
                continue
            if "martial_weapons" in proficiencies and is_martial:
                options.append({"id": weapon["id"], "label": self._label(weapon)})
                continue
            if "martial_finesse_or_light_only" in proficiencies and is_martial and weapon_properties.intersection({"finesse", "light"}):
                options.append({"id": weapon["id"], "label": self._label(weapon)})
                continue
            if weapon.get("id") in proficiencies:
                options.append({"id": weapon["id"], "label": self._label(weapon)})

        return self._dedupe_options(options)

    def _collect_current_skill_proficiencies(self, state: dict[str, Any]) -> set[str]:
        normalized_state = self.normalize_character_creation_state(state)
        skills: set[str] = set()

        background = self.background_by_id.get(str(normalized_state.get("background_id") or ""), {})
        skills.update(str(skill) for skill in background.get("skill_proficiencies", []) if skill)

        species = self.species_by_id.get(str(normalized_state.get("species_id") or ""), {})
        for trait in species.get("traits_level_1", []) if isinstance(species, dict) else []:
            if not isinstance(trait, dict):
                continue
            gain_skill = trait.get("gain_skill_proficiency")
            if isinstance(gain_skill, dict):
                skills.update(str(skill) for skill in gain_skill.get("from", []) if skill)

        class_id = str(normalized_state.get("class_id") or "")
        class_rule = self._find_class_rule(class_id)
        selected_ids = set(self._to_string_list(normalized_state.get("selected_class_choice_ids")))
        for choice in class_rule.get("choices", []):
            if not isinstance(choice, dict) or choice.get("choice_type") != "skill_proficiency":
                continue
            valid_options = {str(option.get("id")) for option in self._resolve_choice_options(choice, normalized_state)}
            skills.update(selected_ids.intersection(valid_options))

        return {skill for skill in skills if skill in self.skill_by_id}

    @staticmethod
    def _ability_modifier(score: int) -> int:
        return (int(score) - 10) // 2

    @staticmethod
    def _merge_unique(target: list[str], values: list[str]) -> None:
        seen = set(target)
        for value in values:
            token = str(value)
            if token and token not in seen:
                target.append(token)
                seen.add(token)

    def _extract_selected_ids_for_choice(self, choice: dict[str, Any], state: dict[str, Any], selection_key: str) -> list[str]:
        selected_pool = self._to_string_list(state.get(selection_key))
        selected_spells_by_choice = state.get("selected_spell_ids_by_choice", {})
        choice_id = str(choice.get("id") or "")
        choose_count = int(choice.get("choose", 1) or 1)

        if choice_id and isinstance(selected_spells_by_choice, dict):
            by_choice = selected_spells_by_choice.get(choice_id)
            if isinstance(by_choice, list):
                raw_values = self._to_string_list(by_choice)
                return raw_values[:choose_count]

        options = self._resolve_choice_options(choice, state)
        option_ids = {str(option.get("id")) for option in options if isinstance(option, dict) and option.get("id")}
        selected_for_choice: list[str] = []
        for selection in selected_pool:
            if selection not in option_ids:
                continue
            if selection in selected_for_choice and bool(choice.get("duplicates_not_allowed", True)):
                continue
            selected_for_choice.append(selection)
            if len(selected_for_choice) >= choose_count:
                break
        return selected_for_choice

    def apply_background_choices(self, state: dict[str, Any], output: dict[str, Any]) -> None:
        background = self.background_by_id.get(str(state.get("background_id") or ""), {})
        self._merge_unique(output["languages"], self._to_string_list(state.get("language_ids")))
        self._merge_unique(output["skills"], self._to_string_list(background.get("skill_proficiencies")))
        tool_prof = background.get("tool_proficiency")
        if isinstance(tool_prof, dict):
            self._merge_unique(output["tools"], self._to_string_list(tool_prof.get("fixed")))

    def apply_species_choices(self, state: dict[str, Any], output: dict[str, Any]) -> None:
        species_id = str(state.get("species_id") or "")
        species = self.species_by_id.get(species_id, {})
        rule = self._find_species_rule(species_id)
        selected_ids = set(self._to_string_list(state.get("selected_species_choice_ids")))

        if not output["size"]:
            size_options = self._to_string_list(species.get("size_options"))
            output["size"] = size_options[0] if size_options else None

        for trait in species.get("traits_level_1", []) if isinstance(species, dict) else []:
            if not isinstance(trait, dict):
                continue
            if trait.get("id") == "darkvision":
                range_feet = int(trait.get("range_feet", 0) or 0)
                output["darkvision_range_feet"] = max(output["darkvision_range_feet"] or 0, range_feet)

        for choice in rule.get("choices", []):
            if not isinstance(choice, dict):
                continue
            selected_for_choice = self._extract_selected_ids_for_choice(choice, state, "selected_species_choice_ids")
            if not selected_for_choice:
                continue
            choice_type = str(choice.get("choice_type") or "")
            if choice_type == "size":
                output["size"] = selected_for_choice[0]
            if choice_type == "skill_proficiency":
                self._merge_unique(output["skills"], selected_for_choice)
            if choice_type == "species_trait_option":
                trait_id = str(choice.get("trait_id") or "")
                selected_option_id = selected_for_choice[0]
                option_details = self._find_species_trait_option(species, trait_id, selected_option_id)
                if option_details:
                    output["resolved_species_trait_options"].append({"trait_id": trait_id, "option_id": selected_option_id})
                    self._apply_species_trait_effects(option_details, output)
            if choice_type == "ability":
                output["species_spellcasting_ability"] = selected_for_choice[0]
            if choice_type == "origin_feat":
                output["selected_bonus_origin_feat_id"] = selected_for_choice[0]
            selected_ids.update(selected_for_choice)

    def apply_class_choices(self, state: dict[str, Any], output: dict[str, Any]) -> None:
        class_id = str(state.get("class_id") or "")
        class_data = self.class_by_id.get(class_id, {})
        class_rule = self._find_class_rule(class_id)
        self._merge_unique(output["skills"], self._to_string_list(class_data.get("skill_proficiencies")))
        self._merge_unique(output["weapon_proficiencies"], self._to_string_list(class_data.get("weapon_proficiencies")))
        self._merge_unique(output["armor_training"], self._to_string_list(class_data.get("armor_training")))

        for choice in class_rule.get("choices", []):
            if not isinstance(choice, dict):
                continue
            selected_for_choice = self._extract_selected_ids_for_choice(choice, state, "selected_class_choice_ids")
            if not selected_for_choice:
                continue
            choice_type = str(choice.get("choice_type") or "")
            if choice_type == "skill_proficiency":
                self._merge_unique(output["skills"], selected_for_choice)
            if choice_type == "tool_proficiency":
                self._merge_unique(output["tools"], selected_for_choice)
            if choice_type == "weapon_mastery":
                for weapon_id in selected_for_choice:
                    weapon = self.equipment_by_id.get(weapon_id, {})
                    mastery_id = str(weapon.get("mastery") or "")
                    output["weapon_masteries"].append({"weapon_id": weapon_id, "mastery_id": mastery_id or None})
            if choice_type == "expertise":
                for skill_id in selected_for_choice:
                    if skill_id in output["skills"] and skill_id not in output["expertise_skills"]:
                        output["expertise_skills"].append(skill_id)
            if choice_type == "eldritch_invocation":
                self._merge_unique(output["eldritch_invocations"], selected_for_choice)
            if choice_type == "feature_option":
                feature = self.class_feature_by_id.get(str(choice.get("feature_id") or ""), {})
                option_id = selected_for_choice[0]
                effects = self._find_feature_option_effects(feature, option_id)
                output["resolved_class_feature_options"].append({"feature_id": feature.get("id"), "option_id": option_id})
                self._apply_feature_effects(effects, output)

    def apply_feat_choices(self, state: dict[str, Any], output: dict[str, Any]) -> None:
        feat_ids = self._to_string_list(state.get("selected_feat_ids"))
        for feat_id in feat_ids:
            feat = self.origin_feat_by_id.get(feat_id, {})
            benefits = feat.get("benefits", {}) if isinstance(feat, dict) else {}
            self._merge_unique(output["feat_ids"], [feat_id])
            if isinstance(benefits, dict):
                self._merge_unique(output["languages"], self._to_string_list(benefits.get("languages")))
                self._merge_unique(output["skills"], self._to_string_list(benefits.get("skill_proficiencies")))

    def _find_feature_option_effects(self, feature: dict[str, Any], option_id: str) -> dict[str, Any]:
        selection = feature.get("selection", {}) if isinstance(feature, dict) else {}
        for option in selection.get("options", []) if isinstance(selection, dict) else []:
            if isinstance(option, dict) and str(option.get("id")) == option_id:
                return option.get("effects", {}) if isinstance(option.get("effects"), dict) else {}
        return {}

    def _find_species_trait_option(self, species: dict[str, Any], trait_id: str, option_id: str) -> dict[str, Any]:
        for trait in species.get("traits_level_1", []) if isinstance(species, dict) else []:
            if not isinstance(trait, dict) or str(trait.get("id")) != trait_id:
                continue
            for option in trait.get("options", []) if isinstance(trait.get("options"), list) else []:
                if isinstance(option, dict) and str(option.get("id")) == option_id:
                    return option
        return {}

    def _apply_feature_effects(self, effects: dict[str, Any], output: dict[str, Any]) -> None:
        if not isinstance(effects, dict):
            return
        self._merge_unique(output["weapon_proficiencies"], self._to_string_list(effects.get("gain_weapon_proficiencies")))
        self._merge_unique(output["armor_training"], self._to_string_list(effects.get("gain_armor_training")))
        extra_cantrip = int(effects.get("gain_extra_cantrip_from_class_list", 0) or 0)
        if extra_cantrip:
            output["extra_class_cantrips"] += extra_cantrip

    def _apply_species_trait_effects(self, option_details: dict[str, Any], output: dict[str, Any]) -> None:
        benefits = option_details.get("level_1_benefits", {}) if isinstance(option_details, dict) else {}
        if not isinstance(benefits, dict):
            return
        self._merge_unique(output["damage_resistances"], self._to_string_list(benefits.get("damage_resistance")))
        self._merge_unique(output["species_cantrips"], self._to_string_list(benefits.get("cantrips_known")))
        always_prepared = self._to_string_list(benefits.get("always_prepared_spells"))
        for spell_id in always_prepared:
            output["species_granted_spells"].append({"spell_id": spell_id, "source_id": option_details.get("id")})
        speed_bonus = int(benefits.get("speed_bonus_feet", 0) or 0)
        if speed_bonus:
            output["speed"]["walk"] += speed_bonus
        darkvision_override = int(benefits.get("darkvision_range_override_feet", 0) or 0)
        if darkvision_override:
            output["darkvision_range_feet"] = max(output["darkvision_range_feet"] or 0, darkvision_override)

    def build_character_output(self, raw_state: dict[str, Any]) -> dict[str, Any]:
        state = self.normalize_character_creation_state(raw_state)
        class_id = str(state.get("class_id") or "")
        background_id = str(state.get("background_id") or "")
        species_id = str(state.get("species_id") or "")
        class_data = self.class_by_id.get(class_id, {})
        species_data = self.species_by_id.get(species_id, {})

        size_options = self._to_string_list(species_data.get("size_options"))
        output: dict[str, Any] = {
            "class_id": class_id or None,
            "background_id": background_id or None,
            "species_id": species_id or None,
            "size": size_options[0] if size_options else None,
            "speed": {"walk": int((species_data.get("speed") or {}).get("walk", 30))},
            "languages": [],
            "skills": [],
            "tools": [],
            "weapon_proficiencies": [],
            "armor_training": [],
            "damage_resistances": [],
            "darkvision_range_feet": None,
            "weapon_masteries": [],
            "expertise_skills": [],
            "eldritch_invocations": [],
            "resolved_class_feature_options": [],
            "resolved_species_trait_options": [],
            "species_spellcasting_ability": None,
            "species_cantrips": [],
            "species_granted_spells": [],
            "feat_granted_spells": [],
            "feat_ids": [],
            "selected_bonus_origin_feat_id": None,
            "extra_class_cantrips": 0,
        }

        self.apply_background_choices(state, output)
        self.apply_species_choices(state, output)
        self.apply_class_choices(state, output)
        self.apply_feat_choices(state, output)

        base_scores = state.get("base_ability_scores", {})
        constitution_score = int(base_scores.get("constitution", 10) or 10)
        dexterity_score = int(base_scores.get("dexterity", 10) or 10)
        constitution_modifier = self._ability_modifier(constitution_score)
        dexterity_modifier = self._ability_modifier(dexterity_score)
        hit_die = int(class_data.get("hit_die", 8) or 8)

        output["derived"] = {
            "hit_points_max": max(1, hit_die + constitution_modifier),
            "armor_class": 10 + dexterity_modifier,
            "initiative_modifier": dexterity_modifier,
        }
        return output

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
            "required_choices_summary": self._build_required_choices_summary(required_choices),
        }

    def get_class_payload(self, class_id: str, state: dict[str, Any]) -> dict[str, Any]:
        class_data = self.class_by_id.get(class_id, {})
        class_rule = self._find_class_rule(class_id)
        automatic_gains = {
            "saving_throw_proficiencies": class_data.get("saving_throw_proficiencies", []),
            "weapon_proficiencies": class_data.get("weapon_proficiencies", []),
            "armor_training": class_data.get("armor_training", []),
            "features_level_1": class_data.get("level_1_features", []),
            "features_level_1_details": self._expand_ids(class_data.get("level_1_features", []), self.class_feature_by_id),
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
            "auto_granted_summary": self._build_auto_granted_summary(automatic_gains),
            "required_choices": required,
            "required_choices_summary": self._build_required_choices_summary(required),
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
        automatic_gains = {
            "skill_proficiencies": bg.get("skill_proficiencies", []),
            "tool_proficiency": bg.get("tool_proficiency"),
            "origin_feat": origin_feat,
        }
        return {
            "background": bg,
            "automatic_gains": automatic_gains,
            "auto_granted_summary": self._build_auto_granted_summary(automatic_gains),
            "origin_feat_details": origin_feat_details,
            "origin_feat_payload": origin_feat_payload,
            "ability_score_options": bg.get("ability_score_options", {}),
            "required_choices": required_choices,
            "required_choices_summary": self._build_required_choices_summary(required_choices),
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
        automatic_gains = {
            "traits_level_1": species.get("traits_level_1", []),
            "size_options": species.get("size_options", []),
            "speed": species.get("speed"),
        }
        return {
            "species": species,
            "automatic_gains": automatic_gains,
            "auto_granted_summary": self._build_auto_granted_summary(automatic_gains),
            "required_choices": required,
            "required_choices_summary": self._build_required_choices_summary(required),
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

    @staticmethod
    def _to_string_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if item]

    @staticmethod
    def _normalize_background_bonus_mode(mode: Any) -> str | None:
        if not mode:
            return None
        normalized = str(mode).strip()
        aliases = {
            "2-1": "increase_one_by_2_and_one_by_1",
            "+2/+1": "increase_one_by_2_and_one_by_1",
            "1-1-1": "increase_all_three_by_1",
            "+1/+1/+1": "increase_all_three_by_1",
        }
        return aliases.get(normalized, normalized)

    @staticmethod
    def _normalize_background_allocations(raw_allocations: Any) -> list[dict[str, Any]]:
        if not isinstance(raw_allocations, list):
            return []
        normalized: list[dict[str, Any]] = []
        for entry in raw_allocations:
            if isinstance(entry, str):
                normalized.append({"ability": entry, "bonus": 1})
                continue
            if isinstance(entry, dict):
                ability = entry.get("ability") or entry.get("id")
                bonus = entry.get("bonus", 1)
                if ability:
                    try:
                        parsed_bonus = int(bonus)
                    except (TypeError, ValueError):
                        parsed_bonus = 1
                    normalized.append({"ability": str(ability), "bonus": parsed_bonus})
        return normalized

    def normalize_character_creation_state(self, state: dict[str, Any] | None) -> dict[str, Any]:
        """Normalise le payload du builder vers un contrat unique."""
        raw_state = state if isinstance(state, dict) else {}
        normalized: dict[str, Any] = dict(BUILDER_STATE_DEFAULTS)

        for raw_key, raw_value in raw_state.items():
            canonical_key = BUILDER_STATE_ALIASES.get(str(raw_key), str(raw_key))
            if canonical_key not in normalized:
                continue
            normalized[canonical_key] = raw_value

        normalized["class_id"] = str(normalized["class_id"]) if normalized.get("class_id") else None
        normalized["background_id"] = str(normalized["background_id"]) if normalized.get("background_id") else None
        normalized["species_id"] = str(normalized["species_id"]) if normalized.get("species_id") else None
        normalized["selected_origin_feat_id"] = (
            str(normalized["selected_origin_feat_id"]) if normalized.get("selected_origin_feat_id") else None
        )
        normalized["ability_score_method"] = (
            str(normalized["ability_score_method"]) if normalized.get("ability_score_method") else None
        )

        for key in (
            "language_ids",
            "selected_class_choice_ids",
            "selected_species_choice_ids",
            "selected_feat_choice_ids",
            "selected_feat_ids",
            "selected_equipment_ids",
            "selected_ability_bonus_ids",
        ):
            normalized[key] = self._to_string_list(normalized.get(key))

        if not isinstance(normalized.get("base_ability_scores"), dict):
            normalized["base_ability_scores"] = {}

        allocations = normalized.get("background_ability_bonus_allocations")
        if isinstance(allocations, dict):
            allocations = allocations.get("items", [])
        normalized["background_ability_bonus_allocations"] = allocations if isinstance(allocations, list) else []

        spells_by_choice = normalized.get("selected_spell_ids_by_choice")
        normalized["selected_spell_ids_by_choice"] = spells_by_choice if isinstance(spells_by_choice, dict) else {}

        equipment_by_slot = normalized.get("selected_equipment_choices_by_slot")
        normalized["selected_equipment_choices_by_slot"] = equipment_by_slot if isinstance(equipment_by_slot, dict) else {}

        return normalized

    def validate_character_creation_submission(self, state: dict[str, Any]) -> list[str]:
        state = self.normalize_character_creation_state(state)
        errors: list[str] = []
        class_id = state.get("class_id")
        background_id = state.get("background_id")
        species_id = state.get("species_id")

        if not class_id:
            errors.append("La classe est obligatoire.")
        elif str(class_id) not in self.class_by_id:
            errors.append("La classe sélectionnée est invalide.")

        if not background_id:
            errors.append("Le background est obligatoire.")
        elif str(background_id) not in self.background_by_id:
            errors.append("Le background sélectionné est invalide.")

        if not species_id:
            errors.append("L'espèce est obligatoire.")
        elif str(species_id) not in self.species_by_id:
            errors.append("L'espèce sélectionnée est invalide.")

        language_ids = self._to_string_list(state.get("language_ids"))
        if len(language_ids) != len(set(language_ids)):
            errors.append("Les langues ne peuvent pas contenir de doublons.")

        if background_id and str(background_id) in self.background_by_id:
            ability_payload = self.get_ability_score_payload(state)
            ability_options = ability_payload.get("background_ability_score_options") or {}
            allowed_modes = set()
            if isinstance(ability_options, dict):
                if isinstance(ability_options.get("allocation_modes"), list):
                    allowed_modes = {str(mode) for mode in ability_options.get("allocation_modes", []) if mode}
                increase_rule = str(ability_options.get("increase_rule", ""))
                if not allowed_modes and "increase_one_by_2_and_one_by_1" in increase_rule:
                    allowed_modes = {"increase_one_by_2_and_one_by_1", "increase_all_three_by_1"}
            selected_mode = self._normalize_background_bonus_mode(state.get("background_ability_bonus_mode"))
            if allowed_modes and selected_mode and selected_mode not in allowed_modes:
                errors.append("Le mode de bonus d'origine est invalide pour ce background.")

            raw_allocations = state.get("background_ability_bonus_allocations")
            if raw_allocations is not None and not isinstance(raw_allocations, list):
                errors.append("Les allocations de bonus d'origine sont invalides.")
            allocations = self._normalize_background_allocations(raw_allocations)
            allowed_abilities = {
                str(ability)
                for ability in (ability_options.get("allowed", []) if isinstance(ability_options, dict) else [])
                if ability
            }
            if allocations and allowed_abilities and any(allocation.get("ability") not in allowed_abilities for allocation in allocations):
                errors.append("Les allocations de bonus d'origine contiennent des capacités non autorisées.")
            if selected_mode == "increase_one_by_2_and_one_by_1":
                bonuses = sorted((int(allocation.get("bonus", 0)) for allocation in allocations), reverse=True)
                abilities = [allocation.get("ability") for allocation in allocations]
                if not (bonuses == [2, 1] and len(abilities) == len(set(abilities)) == 2):
                    errors.append("Les allocations de bonus d'origine ne respectent pas le mode +2/+1.")
            if selected_mode == "increase_all_three_by_1":
                bonuses = [int(allocation.get("bonus", 0)) for allocation in allocations]
                abilities = [allocation.get("ability") for allocation in allocations]
                if not (len(allocations) == 3 and all(bonus == 1 for bonus in bonuses) and len(abilities) == len(set(abilities)) == 3):
                    errors.append("Les allocations de bonus d'origine ne respectent pas le mode +1/+1/+1.")

        ability_score_method = state.get("ability_score_method")
        available_methods = {
            str(method.get("id"))
            for method in self.starting_ability_score_methods
            if isinstance(method, dict) and method.get("id")
        }
        if ability_score_method and str(ability_score_method) not in available_methods:
            errors.append("La méthode de caractéristiques est invalide.")

        selected_spell_ids_by_choice = state.get("selected_spell_ids_by_choice")
        if selected_spell_ids_by_choice is not None and not isinstance(selected_spell_ids_by_choice, dict):
            errors.append("Le format des choix de sorts est invalide.")

        selected_equipment_choices_by_slot = state.get("selected_equipment_choices_by_slot")
        if selected_equipment_choices_by_slot is not None and not isinstance(selected_equipment_choices_by_slot, dict):
            errors.append("Le format des choix d'équipement est invalide.")

        selected_equipment_ids = self._to_string_list(state.get("selected_equipment_ids"))
        if selected_equipment_ids and len(selected_equipment_ids) != len(set(selected_equipment_ids)):
            errors.append("Les équipements sélectionnés ne peuvent pas contenir de doublons.")

        return errors

    def _resolve_equipment_options(self, options: list[Any], state: dict[str, Any]) -> list[dict[str, Any]]:
        def resolve_rule_payload(
            rule: dict[str, Any],
            *,
            item_id: str | None = None,
            choose: int | None = None,
        ) -> dict[str, Any] | None:
            if not isinstance(rule, dict):
                return None
            rule_id = str(rule.get("id") or item_id or "").strip()
            quantity = int(choose if choose is not None else rule.get("quantity", 1))
            choice_from_category = rule.get("choice_from_category")
            if choice_from_category:
                return {
                    "type": "choice_from_category",
                    "id": rule_id or str(choice_from_category),
                    "choose": quantity,
                    "options": self._resolve_subchoice_catalog(str(choice_from_category), state),
                }
            choice_from_catalogs = rule.get("choice_from_catalogs")
            if isinstance(choice_from_catalogs, list):
                merged_options: list[dict[str, Any]] = []
                for catalog_id in choice_from_catalogs:
                    merged_options.extend(self._resolve_subchoice_catalog(str(catalog_id), state))
                return {
                    "type": "choice_from_catalogs",
                    "id": rule_id or "_".join(str(catalog_id) for catalog_id in choice_from_catalogs),
                    "choose": quantity,
                    "options": self._dedupe_options(merged_options),
                }
            return None

        def resolve_fixed_item_payload(item_id: str, quantity: int = 1) -> dict[str, Any]:
            item = self.equipment_by_id.get(item_id, {})
            payload: dict[str, Any] = {
                "type": "fixed_item",
                "id": item_id,
                "choose": quantity,
                "options": [],
                "label": self._label(item) or item_id,
            }
            if quantity > 1:
                payload["quantity"] = quantity
            return payload

        resolved = []
        for option in options or []:
            if not isinstance(option, dict):
                continue
            items = []
            for raw_item in option.get("items", []):
                if isinstance(raw_item, str):
                    category_items = self._resolve_subchoice_catalog(raw_item, state)
                    if category_items:
                        items.append(
                            {
                                "type": "choice_from_category",
                                "id": raw_item,
                                "choose": 1,
                                "options": category_items,
                            }
                        )
                        continue
                    items.append(resolve_fixed_item_payload(raw_item))
                elif isinstance(raw_item, dict) and raw_item.get("choice_from_category"):
                    resolved_item = resolve_rule_payload(
                        {
                            "id": raw_item.get("id"),
                            "choice_from_category": raw_item.get("choice_from_category"),
                            "quantity": raw_item.get("quantity", 1),
                        },
                        item_id=str(raw_item.get("id") or raw_item.get("choice_from_category") or ""),
                    )
                    if resolved_item:
                        items.append(resolved_item)
                elif isinstance(raw_item, dict) and isinstance(raw_item.get("choice_from_catalogs"), list):
                    resolved_item = resolve_rule_payload(
                        {
                            "id": raw_item.get("id"),
                            "choice_from_catalogs": raw_item.get("choice_from_catalogs"),
                            "quantity": raw_item.get("quantity", 1),
                        },
                        item_id=str(raw_item.get("id") or ""),
                    )
                    if resolved_item:
                        items.append(resolved_item)
                elif isinstance(raw_item, dict) and raw_item.get("equipment_choice_rule_id"):
                    rule = self.equipment_choice_rule_by_id.get(str(raw_item.get("equipment_choice_rule_id")), {})
                    resolved_item = resolve_rule_payload(
                        {
                            **rule,
                            "id": raw_item.get("id") or raw_item.get("equipment_choice_rule_id"),
                            "quantity": raw_item.get("quantity", rule.get("quantity", 1)),
                        },
                        item_id=str(raw_item.get("id") or raw_item.get("equipment_choice_rule_id") or ""),
                    )
                    if resolved_item:
                        items.append(resolved_item)
                elif isinstance(raw_item, dict) and raw_item.get("id"):
                    items.append(resolve_fixed_item_payload(str(raw_item.get("id")), int(raw_item.get("quantity", 1))))
            gold_amount = int(option.get("gold", 0) or 0)
            if gold_amount > 0:
                items.append(
                    {
                        "type": "gold_alternative",
                        "id": f"{option.get('id')}_gold",
                        "choose": 1,
                        "options": [],
                        "gold": gold_amount,
                    }
                )
            resolved.append({"id": option.get("id"), "label": option.get("label"), "items": items, "gold": gold_amount})
        return resolved

    @property
    def equipment_by_id(self) -> dict[str, dict[str, Any]]:
        combined = [
            *self.equipment_items,
            *self.equipment_items_adventuring_gear,
            *self.starting_equipment_packs,
            *self.weapons_catalog,
            *self.tools,
        ]
        return self._index(combined)


@lru_cache(maxsize=1)
def get_character_builder_service() -> CharacterBuilderService:
    return CharacterBuilderService()
