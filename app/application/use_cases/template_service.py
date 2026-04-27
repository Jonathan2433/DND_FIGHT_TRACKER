# Migrated to application layer
"""Service métier pour la gestion des templates"""
import json
import logging
import os
import uuid
from flask import current_app, has_app_context
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import CharacterTemplate, EncounterTemplate, Combatant
from app.models.user import User
from app.utils import MONSTER_TEMPLATES, allowed_file
from app.utils.dnd5_rules import resolve_character_creation
from app.utils.spell_catalog import get_cantrips, get_spells_for_level
from app.utils.character_builder_engine import get_rules_loaders
from app.services.character_builder_service import get_character_builder_service
from app.application.use_cases.notification_service import NotificationService
from app.application.use_cases.character_sheet_pdf_service import CharacterSheetPdfService


class TemplateService:
    ABILITY_ALIASES = {
        "force": "strength",
        "strength": "strength",
        "dextérité": "dexterity",
        "dexterite": "dexterity",
        "dexterity": "dexterity",
        "constitution": "constitution",
        "intelligence": "intelligence",
        "sagesse": "wisdom",
        "wisdom": "wisdom",
        "charisme": "charisma",
        "charisma": "charisma",
    }
    CANONICAL_ABILITIES = {"strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"}

    @staticmethod
    def _normalize_language_label(language_value):
        """Normalise les identifiants de langue du funnel vers les libellés attendus en base."""
        if not language_value:
            return None
        normalized = str(language_value).strip()
        if not normalized:
            return None

        lowered = normalized.lower()
        canonical_map = {
            'common': 'Commun',
            'commun': 'Commun',
        }
        return canonical_map.get(lowered, normalized.title())

    """Service pour la gestion des templates de personnages et rencontres"""
    ARMOR_MASTERY_BY_CLASS = {
        "barbare": {"light", "medium", "shield"},
        "barde": {"light"},
        "clerc": {"light", "medium", "shield"},
        "druide": {"light", "shield"},
        "guerrier": {"light", "medium", "heavy", "shield"},
        "moine": set(),
        "paladin": {"light", "medium", "heavy", "shield"},
        "rodeur": {"light", "medium", "shield"},
        "roublard": {"light"},
        "ensorceleur": set(),
        "occultiste": {"light"},
        "magicien": set(),
        "barbarian": {"light", "medium", "shield"},
        "bard": {"light"},
        "cleric": {"light", "medium", "shield"},
        "druid": {"light", "shield"},
        "fighter": {"light", "medium", "heavy", "shield"},
        "monk": set(),
        "ranger": {"light", "medium", "shield"},
        "rogue": {"light"},
        "sorcerer": set(),
        "warlock": {"light"},
        "wizard": set(),
    }
    WEAPON_MASTERY_BY_CLASS = {
        "barbare": {"simple": True, "martial": True, "martial_allowed": None},
        "barde": {"simple": True, "martial": False, "martial_allowed": None},
        "clerc": {"simple": True, "martial": False, "martial_allowed": None},
        "druide": {"simple": True, "martial": False, "martial_allowed": None},
        "guerrier": {"simple": True, "martial": True, "martial_allowed": None},
        "moine": {"simple": True, "martial": True, "martial_allowed": {"Epee courte", "Arbalete de poing"}},
        "paladin": {"simple": True, "martial": True, "martial_allowed": None},
        "rodeur": {"simple": True, "martial": True, "martial_allowed": None},
        "roublard": {"simple": True, "martial": True, "martial_allowed": {"Epee courte", "Arc long", "Arbalete de poing"}},
        "ensorceleur": {"simple": True, "martial": False, "martial_allowed": None},
        "occultiste": {"simple": True, "martial": False, "martial_allowed": None},
        "magicien": {"simple": True, "martial": False, "martial_allowed": None},
        "barbarian": {"simple": True, "martial": True, "martial_allowed": None},
        "bard": {"simple": True, "martial": False, "martial_allowed": None},
        "cleric": {"simple": True, "martial": False, "martial_allowed": None},
        "druid": {"simple": True, "martial": False, "martial_allowed": None},
        "fighter": {"simple": True, "martial": True, "martial_allowed": None},
        "monk": {"simple": True, "martial": True, "martial_allowed": {"Epee courte", "Arbalete de poing"}},
        "ranger": {"simple": True, "martial": True, "martial_allowed": None},
        "rogue": {"simple": True, "martial": True, "martial_allowed": {"Epee courte", "Arc long", "Arbalete de poing"}},
        "sorcerer": {"simple": True, "martial": False, "martial_allowed": None},
        "warlock": {"simple": True, "martial": False, "martial_allowed": None},
        "wizard": {"simple": True, "martial": False, "martial_allowed": None},
    }
    WEAPON_CATEGORY_BY_LOADOUT = {
        "Epee longue": "martial",
        "Epee courte": "martial",
        "Dague": "simple",
        "Hachette": "simple",
        "Marteau leger": "simple",
        "Lance": "simple",
        "Arc court": "simple",
        "Arc long": "martial",
        "Arbalete legere": "simple",
        "Arbalete de poing": "martial",
    }
    ARMOR_CATEGORIES_BY_LOADOUT = {
        "Sans armure": {"none"},
        "Armure matelassee": {"light"},
        "Armure de cuir": {"light"},
        "Armure de cuir cloutee": {"light"},
        "Chemise de mailles": {"medium"},
        "Cuirasse": {"medium"},
        "Demi-plate": {"medium"},
        "Cotte de mailles": {"heavy"},
        "Harnois": {"heavy"},
        "Bouclier": {"shield"},
        "Armure de cuir + Bouclier": {"light", "shield"},
        "Chemise de mailles + Bouclier": {"medium", "shield"},
        "Cotte de mailles + Bouclier": {"heavy", "shield"},
    }
    ARMOR_BASE_AC_BY_LOADOUT = {
        "Sans armure": 10,
        "Armure matelassee": 11,
        "Armure de cuir": 11,
        "Armure de cuir cloutee": 12,
        "Chemise de mailles": 13,
        "Cuirasse": 14,
        "Demi-plate": 15,
        "Cotte de mailles": 16,
        "Harnois": 18,
        "Bouclier": 10,
    }
    RANGED_WEAPON_HINTS = ("arc", "arbalete", "fronde", "javelot", "sarbacane", "dard")
    SKILL_PROFICIENCY_LIMITS_BY_CLASS = {
        "artificier": 2,
        "barbarian": 2,
        "barbare": 2,
        "bard": 3,
        "barde": 3,
        "cleric": 2,
        "clerc": 2,
        "druid": 2,
        "druide": 2,
        "fighter": 2,
        "guerrier": 2,
        "monk": 2,
        "moine": 2,
        "paladin": 2,
        "ranger": 3,
        "rodeur": 3,
        "rôdeur": 3,
        "rogue": 4,
        "roublard": 4,
        "sorcerer": 2,
        "ensorceleur": 2,
        "warlock": 2,
        "occultiste": 2,
        "wizard": 2,
        "magicien": 2,
    }
    SPELLCASTING_ABILITIES_BY_CLASS = {
        "artificier": "INT",
        "bard": "CHA",
        "barde": "CHA",
        "clerc": "WIS",
        "cleric": "WIS",
        "druide": "WIS",
        "druid": "WIS",
        "ensorceleur": "CHA",
        "magicien": "INT",
        "occultiste": "CHA",
        "paladin": "CHA",
        "ranger": "WIS",
        "rodeur": "WIS",
        "rôdeur": "WIS",
        "sorcerer": "CHA",
        "warlock": "CHA",
        "wizard": "INT",
    }
    SPELL_SELECTION_LIMITS_BY_CLASS = {
        "artificier": {"cantrips": 2, "level_1_spells": 2},
        "bard": {"cantrips": 2, "level_1_spells": 4},
        "barde": {"cantrips": 2, "level_1_spells": 4},
        "cleric": {"cantrips": 3, "level_1_spells": 4},
        "clerc": {"cantrips": 3, "level_1_spells": 4},
        "druid": {"cantrips": 2, "level_1_spells": 4},
        "druide": {"cantrips": 2, "level_1_spells": 4},
        "sorcerer": {"cantrips": 4, "level_1_spells": 2},
        "ensorceleur": {"cantrips": 4, "level_1_spells": 2},
        "warlock": {"cantrips": 2, "level_1_spells": 2},
        "occultiste": {"cantrips": 2, "level_1_spells": 2},
        "wizard": {"cantrips": 3, "level_1_spells": 4},
        "magicien": {"cantrips": 3, "level_1_spells": 4},
        "paladin": {"cantrips": 0, "level_1_spells": 2},
        "ranger": {"cantrips": 0, "level_1_spells": 2},
        "rodeur": {"cantrips": 0, "level_1_spells": 2},
        "rôdeur": {"cantrips": 0, "level_1_spells": 2},
    }
    CLASS_ALIAS_TO_ENGLISH = {
        "artificier": "artificer",
        "barde": "bard",
        "clerc": "cleric",
        "druide": "druid",
        "ensorceleur": "sorcerer",
        "magicien": "wizard",
        "occultiste": "warlock",
        "rodeur": "ranger",
        "roublard": "rogue",
        "barbare": "barbarian",
        "guerrier": "fighter",
        "moine": "monk",
    }
    LEVEL_ONE_SPELLS_BY_CLASS = {
        "bard": {
            "animal friendship", "bane", "charm person", "color spray", "command",
            "cure wounds", "detect magic", "detect thoughts", "disguise self",
            "dissonant whispers", "faerie fire", "feather fall", "healing word",
            "heroism", "identify", "illusory script", "longstrider", "silent image",
            "sleep", "speak with animals", "tasha's hideous laughter", "thunderwave",
            "unseen servant",
        },
        "cleric": {
            "bane", "bless", "command", "create or destroy water", "cure wounds",
            "detect evil and good", "detect magic", "detect poison and disease",
            "guiding bolt", "healing word", "inflict wounds",
            "protection from evil and good", "purify food and drink", "sanctuary",
            "shield of faith",
        },
        "druid": {
            "animal friendship", "animal messenger", "charm person", "create or destroy water",
            "cure wounds", "detect magic", "detect poison and disease", "entangle",
            "faerie fire", "fog cloud", "goodberry", "healing word", "ice knife",
            "jump", "longstrider", "purify food and drink", "thunderwave",
        },
        "sorcerer": {
            "burning hands", "charm person", "chromatic orb", "color spray",
            "detect magic", "disguise self", "expeditious retreat", "false life",
            "feather fall", "fog cloud", "ice knife", "jump", "mage armor",
            "magic missile", "ray of sickness", "shield", "sleep", "thunderwave",
        },
        "warlock": {
            "bane", "charm person", "comprehend languages", "detect magic",
            "expeditious retreat", "hellish rebuke", "hex", "illusory script",
            "protection from evil and good", "speak with animals",
            "tasha's hideous laughter", "unseen servant",
        },
        "wizard": {
            "alarm", "burning hands", "charm person", "chromatic orb", "color spray",
            "comprehend languages", "detect magic", "disguise self",
            "expeditious retreat", "false life", "feather fall", "find familiar",
            "fog cloud", "grease", "ice knife", "identify", "illusory script",
            "jump", "mage armor", "magic missile", "protection from evil and good",
            "ray of sickness", "shield", "sleep", "tasha's hideous laughter",
            "thunderwave", "unseen servant",
        },
        "paladin": {
            "bless", "command", "cure wounds", "detect evil and good", "detect magic",
            "detect poison and disease", "divine favor", "heroism",
            "protection from evil and good", "purify food and drink",
            "searing smite", "shield of faith",
        },
        "ranger": {
            "alarm", "animal friendship", "animal messenger", "cure wounds",
            "detect magic", "detect poison and disease", "ensnaring strike",
            "entangle", "fog cloud", "jump", "longstrider", "speak with animals",
        },
    }

    @staticmethod
    def _normalize_spell_name(value):
        return (value or "").strip().lower().replace("’", "'").replace("`", "'")

    @staticmethod
    def _skill_label_from_id(skill_id):
        skill = get_character_builder_service().skill_by_id.get(str(skill_id), {})
        if isinstance(skill, dict):
            return (
                skill.get("name_fr")
                or skill.get("name")
                or skill.get("name_en")
                or skill.get("id")
            )
        return None

    @classmethod
    def _normalize_skill_proficiencies(cls, form_data, resolved_character=None):
        """Normalise les competences maitrisees depuis les checkboxes (ou texte legacy)."""
        resolved_skill_ids = []
        if isinstance(resolved_character, dict):
            resolved_skill_ids = [str(item) for item in resolved_character.get('resolved_skill_proficiencies', []) if item]
        if resolved_skill_ids:
            resolved_labels = [label for label in (cls._skill_label_from_id(skill_id) for skill_id in resolved_skill_ids) if label]
            if resolved_labels:
                return ", ".join(dict.fromkeys(resolved_labels))

        selected_skills = [item.strip() for item in form_data.getlist('skill_proficiencies') if item and item.strip()]
        if selected_skills:
            return ", ".join(dict.fromkeys(selected_skills))

        legacy_value = (form_data.get('skill_proficiencies') or '').strip()
        if not legacy_value:
            return None
        split_values = [token.strip() for token in legacy_value.replace(';', ',').split(',') if token.strip()]
        return ", ".join(dict.fromkeys(split_values)) if split_values else None

    @staticmethod
    def _normalize_class_name(value):
        return (value or '').strip().lower().replace('ô', 'o').replace('é', 'e').replace('è', 'e')

    @classmethod
    def _canonical_class_name(cls, value):
        normalized = cls._normalize_class_name(value)
        return cls.CLASS_ALIAS_TO_ENGLISH.get(normalized, normalized)

    @classmethod
    def _validate_skill_proficiencies_limit(cls, character_class, normalized_skill_proficiencies, form_data=None):
        def _safe_getlist(source, key):
            getter = getattr(source, "getlist", None)
            if callable(getter):
                try:
                    return [item for item in getter(key) if item]
                except Exception:
                    return []
            return []

        def _normalize_scope(raw_scope):
            scope = str(raw_scope or "").strip().lower()
            if scope in {"class", "background", "species"}:
                return scope
            if scope == "spell":
                return "class"
            if scope.startswith("feat_"):
                return "feat"
            return ""

        if form_data is not None:
            structured_choices = cls._safe_parse_json_list(form_data.get("feat_choices"))
            class_skill_choices_by_id = {}
            for entry in structured_choices:
                if not isinstance(entry, dict):
                    continue
                scope = _normalize_scope(entry.get("scope"))
                if scope != "class":
                    continue
                if str(entry.get("choice_type") or "").strip() != "skill_proficiency":
                    continue
                choice_id = str(entry.get("choice_id") or "").strip()
                value = str(entry.get("value") or "").strip()
                if not choice_id or not value:
                    continue
                class_skill_choices_by_id.setdefault(choice_id, [])
                if value not in class_skill_choices_by_id[choice_id]:
                    class_skill_choices_by_id[choice_id].append(value)

            if class_skill_choices_by_id:
                service = get_character_builder_service()
                class_id = character_class or form_data.get("character_class")
                class_state = service.normalize_character_creation_state(
                    {
                        "class_id": class_id,
                        "selected_class_choice_ids": _safe_getlist(form_data, "selected_class_choice_ids"),
                    }
                )
                class_payload = service.get_class_payload(class_id, class_state) if class_id else {}
                required_choices = class_payload.get("required_choices", []) if isinstance(class_payload, dict) else []
                for choice in required_choices:
                    if not isinstance(choice, dict):
                        continue
                    if str(choice.get("type") or "").strip() != "skill_proficiency":
                        continue
                    if not bool(choice.get("required", True)):
                        continue
                    choice_id = str(choice.get("id") or "")
                    choose = int(choice.get("choose", 1) or 1)
                    selected_for_choice = class_skill_choices_by_id.get(choice_id, [])
                    if len(selected_for_choice) != choose:
                        raise ValueError(
                            f"Choix requis incomplet ({choice_id}): {len(selected_for_choice)}/{choose}."
                        )
                return

        if not normalized_skill_proficiencies:
            return
        selected_skills = [token.strip() for token in normalized_skill_proficiencies.split(',') if token.strip()]
        selected_count = len(selected_skills)
        class_key = cls._normalize_class_name(character_class)
        max_allowed = cls.SKILL_PROFICIENCY_LIMITS_BY_CLASS.get(class_key, 2)
        if selected_count > max_allowed:
            raise ValueError(
                f"La classe '{character_class}' ne peut choisir que {max_allowed} competences maitrisees au niveau 1 (selection actuelle: {selected_count})."
            )

    @classmethod
    def _derive_spellcasting_stats(cls, character_class, level, resolved_character):
        """Calcule la stat de lancement, DD des sorts et bonus d'attaque."""
        normalized_class = (character_class or '').strip().lower().replace('ô', 'o').replace('é', 'e').replace('è', 'e')
        ability_code = cls.SPELLCASTING_ABILITIES_BY_CLASS.get(normalized_class)
        if not ability_code:
            return None, None, None

        ability_field = {
            'STR': 'force',
            'DEX': 'dexterite',
            'CON': 'constitution',
            'INT': 'intelligence',
            'WIS': 'sagesse',
            'CHA': 'charisme',
        }[ability_code]
        ability_score = int(resolved_character.get(ability_field, 10) or 10)
        ability_mod = (ability_score - 10) // 2
        level = int(level or 1)
        proficiency_bonus = 2 + ((max(1, level) - 1) // 4)
        return ability_code, 8 + proficiency_bonus + ability_mod, proficiency_bonus + ability_mod

    @staticmethod
    def _normalize_selected_spells(form_data, field_name):
        selected_spells = [item.strip() for item in form_data.getlist(field_name) if item and item.strip()]
        if selected_spells:
            return ", ".join(dict.fromkeys(selected_spells))
        return None

    @staticmethod
    def _normalize_spell_token(value):
        return (
            str(value or "")
            .strip()
            .lower()
            .replace("’", "'")
            .replace("-", "_")
            .replace(" ", "_")
        )

    @classmethod
    def _build_spell_selection_aliases(cls, valid_spells):
        aliases = {}
        for spell in valid_spells or []:
            if not isinstance(spell, dict):
                continue
            display_name = str(spell.get("name") or "").strip()
            if not display_name:
                continue
            for candidate in (spell.get("name"), spell.get("name_en"), spell.get("id")):
                normalized_candidate = cls._normalize_spell_token(candidate)
                if normalized_candidate and normalized_candidate not in aliases:
                    aliases[normalized_candidate] = display_name
        return aliases

    @classmethod
    def _canonicalize_selected_spells(cls, normalized_spells, valid_spells):
        if not normalized_spells:
            return None
        aliases = cls._build_spell_selection_aliases(valid_spells)
        canonical_values = []
        for raw_value in [item.strip() for item in normalized_spells.split(",") if item.strip()]:
            normalized_value = cls._normalize_spell_token(raw_value)
            canonical_value = aliases.get(normalized_value)
            if canonical_value:
                canonical_values.append(canonical_value)
            else:
                canonical_values.append(raw_value)
        deduped = list(dict.fromkeys(canonical_values))
        return ", ".join(deduped) if deduped else None

    @staticmethod
    def _normalize_choice_scope(raw_scope):
        scope = str(raw_scope or "").strip().lower()
        if scope in {"class", "background", "species", "feat"}:
            return scope
        if scope == "spell":
            return "class"
        if scope.startswith("feat_"):
            return "feat"
        return ""

    @staticmethod
    def _extract_selected_spells_by_choice(form_data):
        """Reconstruit les sélections de sorts canonisées par choice_id."""
        selected_spells_by_choice = {}
        if not form_data:
            return selected_spells_by_choice

        for field_name in ("selected_spell_ids_by_choice_json", "selected_spells_by_choice_json"):
            raw_value = form_data.get(field_name)
            if not raw_value:
                continue
            try:
                parsed = json.loads(raw_value)
            except Exception:
                continue
            if not isinstance(parsed, dict):
                continue
            for choice_id, raw_values in parsed.items():
                if not choice_id:
                    continue
                if isinstance(raw_values, list):
                    values = [str(item).strip() for item in raw_values if str(item).strip()]
                elif raw_values is None:
                    values = []
                else:
                    value = str(raw_values).strip()
                    values = [value] if value else []
                if values:
                    selected_spells_by_choice[str(choice_id)] = list(dict.fromkeys(values))
            if selected_spells_by_choice:
                return selected_spells_by_choice

        feat_choices = TemplateService._safe_parse_json_list(form_data.get("feat_choices"))
        allowed_choice_types = {"spell", "cantrip", "prepared_spell", "spellbook_entry"}
        for entry in feat_choices:
            if not isinstance(entry, dict):
                continue
            scope = str(entry.get("scope") or "").strip()
            choice_type = str(entry.get("choice_type") or "").strip()
            normalized_scope = TemplateService._normalize_choice_scope(scope)
            if normalized_scope not in {"class", "background", "species", "feat"} or choice_type not in allowed_choice_types:
                continue
            choice_id = str(entry.get("choice_id") or "").strip()
            value = str(entry.get("value") or "").strip()
            if not choice_id or not value:
                continue
            selected_spells_by_choice.setdefault(choice_id, [])
            if value not in selected_spells_by_choice[choice_id]:
                selected_spells_by_choice[choice_id].append(value)

        return selected_spells_by_choice

    @staticmethod
    def _uses_choice_based_spell_selection(form_data):
        return bool(TemplateService._extract_selected_spells_by_choice(form_data))

    @staticmethod
    def _validate_selected_spells_exist(normalized_spells, valid_spells, label):
        if not normalized_spells:
            return
        valid_names = {spell["name"] for spell in valid_spells}
        valid_aliases = TemplateService._build_spell_selection_aliases(valid_spells)
        selected_names = [item.strip() for item in normalized_spells.split(",") if item.strip()]
        invalid_names = []
        for name in selected_names:
            if name in valid_names:
                continue
            if TemplateService._normalize_spell_token(name) in valid_aliases:
                continue
            invalid_names.append(name)
        invalid_names = list(dict.fromkeys(invalid_names))
        if invalid_names:
            raise ValueError(
                f"{label} invalides detectes dans la selection: {', '.join(invalid_names)}."
            )

    @classmethod
    def _validate_spell_selection_rules(cls, character_class, selected_cantrips, selected_level_1_spells, cantrip_catalog, level_one_catalog):
        class_key = cls._normalize_class_name(character_class)
        class_key_canonical = cls._canonical_class_name(character_class)
        limits = cls.SPELL_SELECTION_LIMITS_BY_CLASS.get(class_key, {"cantrips": 0, "level_1_spells": 0})

        selected_cantrip_names = [item.strip() for item in (selected_cantrips or '').split(',') if item.strip()]
        selected_level_one_names = [item.strip() for item in (selected_level_1_spells or '').split(',') if item.strip()]

        if len(selected_cantrip_names) > limits["cantrips"]:
            raise ValueError(
                f"La classe '{character_class}' ne peut choisir que {limits['cantrips']} sort(s) mineur(s) au niveau 1."
            )
        if len(selected_level_one_names) > limits["level_1_spells"]:
            raise ValueError(
                f"La classe '{character_class}' ne peut choisir que {limits['level_1_spells']} sort(s) de niveau 1 au niveau 1."
            )

        catalog_index = {spell["name"]: spell for spell in (cantrip_catalog + level_one_catalog)}
        use_json_spell_rules = get_rules_loaders().has_knowledge_base()
        strict_level_one_allow_list = None if use_json_spell_rules else cls.LEVEL_ONE_SPELLS_BY_CLASS.get(class_key_canonical)
        if strict_level_one_allow_list is not None:
            disallowed_level_one = []
            for spell_name in selected_level_one_names:
                spell = catalog_index.get(spell_name) or {}
                normalized_candidates = {
                    cls._normalize_spell_name(spell_name),
                    cls._normalize_spell_name(spell.get("name")),
                    cls._normalize_spell_name(spell.get("name_en")),
                }
                normalized_candidates.discard("")
                if not any(candidate in strict_level_one_allow_list for candidate in normalized_candidates):
                    disallowed_level_one.append(spell_name)

            if disallowed_level_one:
                raise ValueError(
                    f"La classe '{character_class}' ne peut pas preparer ces sorts de niveau 1: {', '.join(disallowed_level_one)}."
                )

        for spell_name in selected_cantrip_names + selected_level_one_names:
            spell = catalog_index.get(spell_name)
            if not spell:
                continue
            raw_classes = [str(item).strip().lower() for item in (spell.get("classes") or []) if str(item).strip()]
            if not raw_classes or class_key_canonical not in raw_classes:
                raise ValueError(
                    f"Le sort '{spell_name}' n'est pas disponible pour la classe '{character_class}'."
                )

    @classmethod
    def _validate_equipment_mastery(cls, character_class, weapon_loadout, armor_loadout):
        class_key = cls._normalize_class_name(character_class)
        weapon_rule = cls.WEAPON_MASTERY_BY_CLASS.get(class_key)
        armor_masteries = cls.ARMOR_MASTERY_BY_CLASS.get(class_key)

        selected_weapon = (weapon_loadout or "").strip()
        if selected_weapon:
            weapon_category = cls.WEAPON_CATEGORY_BY_LOADOUT.get(selected_weapon)
            if weapon_category and weapon_rule:
                if weapon_category == "simple" and not weapon_rule.get("simple"):
                    raise ValueError(
                        f"La classe '{character_class}' ne maitrise pas l'arme '{selected_weapon}'."
                    )
                if weapon_category == "martial":
                    if not weapon_rule.get("martial"):
                        raise ValueError(
                            f"La classe '{character_class}' ne maitrise pas l'arme martiale '{selected_weapon}'."
                        )
                    allowed_list = weapon_rule.get("martial_allowed")
                    if allowed_list is not None and selected_weapon not in allowed_list:
                        raise ValueError(
                            f"La classe '{character_class}' ne peut pas s'equiper avec '{selected_weapon}'."
                        )

        selected_armor = (armor_loadout or "").strip()
        if selected_armor:
            armor_needs = cls.ARMOR_CATEGORIES_BY_LOADOUT.get(selected_armor)
            if armor_needs and armor_masteries is not None:
                required_masteries = {item for item in armor_needs if item != "none"}
                if not required_masteries.issubset(armor_masteries):
                    raise ValueError(
                        f"La classe '{character_class}' ne maitrise pas l'armure/bouclier '{selected_armor}'."
                    )

    @staticmethod
    def _save_uploaded_file(uploaded_file, upload_folder):
        """Sauvegarde un fichier avec un nom unique pour éviter tout écrasement."""
        original_name = secure_filename(uploaded_file.filename or "")
        extension = os.path.splitext(original_name)[1].lower()
        unique_name = f"{uuid.uuid4().hex}{extension}"
        uploaded_file.save(os.path.join(upload_folder, unique_name))
        return unique_name

    @staticmethod
    def _compose_builder_equipment(form_data):
        """Compose un bloc equipement detaille depuis le funnel de creation."""
        inferred_weapon_loadout, inferred_ranged_weapon_loadout = TemplateService._infer_missing_weapon_loadouts(form_data)
        base_equipment = TemplateService._format_equipment_summary(form_data.get('equipment'))
        skill_proficiencies = TemplateService._normalize_skill_proficiencies(form_data) or ''
        expertise_skills = TemplateService._extract_expertise_skills(form_data)
        tool_proficiencies = TemplateService._format_equipment_summary(form_data.get('tool_proficiencies'))
        weapon_loadout = TemplateService._format_loadout_summary(form_data.get('weapon_loadout') or inferred_weapon_loadout)
        ranged_weapon_loadout = TemplateService._format_loadout_summary(
            form_data.get('ranged_weapon_loadout') or inferred_ranged_weapon_loadout
        )
        armor_loadout = TemplateService._format_loadout_summary(form_data.get('armor_loadout'))
        inventory_items = TemplateService._format_equipment_summary(form_data.get('inventory_items'))
        spellbook_notes = (form_data.get('spellbook_notes') or '').strip()

        sections = []
        if base_equipment:
            sections.append(f"Equipement principal: {base_equipment}")
        if weapon_loadout:
            sections.append(f"Arme de corps a corps equipee: {weapon_loadout}")
        if ranged_weapon_loadout:
            sections.append(f"Arme a distance equipee: {ranged_weapon_loadout}")
        if armor_loadout:
            sections.append(f"Armure/Bouclier: {armor_loadout}")
        if inventory_items:
            sections.append(f"Inventaire: {inventory_items}")
        if skill_proficiencies:
            sections.append(f"Competences maitrisees: {skill_proficiencies}")
        if expertise_skills:
            sections.append(f"Expertises: {expertise_skills}")
        if tool_proficiencies:
            sections.append(f"Outils maitrises: {tool_proficiencies}")
        if spellbook_notes:
            sections.append(f"Sorts/Aptitudes: {spellbook_notes}")

        if not sections:
            return None
        return " | ".join(sections)

    @staticmethod
    def _format_equipment_summary(raw_equipment):
        text = str(raw_equipment or '').strip()
        if not text:
            return ''

        formatted_tokens = []
        for raw_token in text.replace(';', ',').split(','):
            label = TemplateService._humanize_equipment_token(raw_token)
            if label and label not in formatted_tokens:
                formatted_tokens.append(label)

        return ", ".join(formatted_tokens)

    @staticmethod
    def _format_loadout_summary(raw_loadout):
        text = str(raw_loadout or '').strip()
        if not text:
            return ''

        chunks = []
        for raw_chunk in text.split('+'):
            tokens = []
            for raw_token in str(raw_chunk or '').replace(';', ',').split(','):
                label = TemplateService._humanize_equipment_token(raw_token)
                if label and label not in tokens:
                    tokens.append(label)
            if tokens:
                chunks.append(", ".join(tokens))
        return " + ".join(chunks)

    @staticmethod
    def _humanize_equipment_token(raw_token):
        token = str(raw_token or '').strip()
        if not token:
            return None

        lowered = token.lower()
        if lowered.startswith('class:'):
            return None
        if lowered.startswith('background:'):
            return None

        equipment_entry = get_character_builder_service().equipment_by_id.get(token)
        if isinstance(equipment_entry, dict):
            return (
                equipment_entry.get('name_fr')
                or equipment_entry.get('name')
                or equipment_entry.get('name_en')
                or equipment_entry.get('id')
            )

        return token

    @classmethod
    def _infer_missing_weapon_loadouts(cls, form_data):
        weapon_loadout = (form_data.get('weapon_loadout') or '').strip()
        ranged_weapon_loadout = (form_data.get('ranged_weapon_loadout') or '').strip()
        if weapon_loadout and ranged_weapon_loadout:
            return weapon_loadout, ranged_weapon_loadout

        labels = cls._extract_equipment_labels(form_data.get('equipment'))
        if not labels:
            return weapon_loadout, ranged_weapon_loadout

        def _is_ranged(label):
            normalized = cls._strip_accents(label).lower()
            return any(hint in normalized for hint in cls.RANGED_WEAPON_HINTS)

        if not ranged_weapon_loadout:
            ranged_weapon_loadout = next((label for label in labels if _is_ranged(label)), "")
        if not weapon_loadout:
            weapon_loadout = next((label for label in labels if not _is_ranged(label)), "")
        return weapon_loadout, ranged_weapon_loadout

    @classmethod
    def _extract_equipment_labels(cls, raw_value):
        labels = []
        for raw_token in str(raw_value or '').replace(';', ',').split(','):
            label = cls._humanize_equipment_token(raw_token)
            if label and label not in labels:
                labels.append(label)
        return labels

    @staticmethod
    def _strip_accents(value):
        return (
            str(value or '')
            .replace('é', 'e')
            .replace('è', 'e')
            .replace('ê', 'e')
            .replace('ë', 'e')
            .replace('à', 'a')
            .replace('â', 'a')
            .replace('ù', 'u')
            .replace('û', 'u')
            .replace('î', 'i')
            .replace('ï', 'i')
            .replace('ô', 'o')
            .replace('ç', 'c')
        )

    @classmethod
    def _apply_armor_loadout_to_ac_base(cls, resolved_character, armor_loadout):
        if not isinstance(resolved_character, dict):
            return resolved_character
        normalized = str(armor_loadout or '').strip()
        if not normalized:
            return resolved_character

        has_shield = "bouclier" in normalized.lower()
        armor_label = normalized.replace(" + Bouclier", "").strip()
        if armor_label == "Bouclier":
            armor_label = "Sans armure"

        base = cls.ARMOR_BASE_AC_BY_LOADOUT.get(armor_label)
        if base is None:
            return resolved_character
        resolved_character['ac_base'] = base + (2 if has_shield else 0)
        return resolved_character

    @staticmethod
    def _extract_expertise_skills(form_data):
        """Extrait les expertises sélectionnées via le payload canonique des choix."""
        if form_data is None:
            return ""

        selected_proficient_skills = {
            token.strip()
            for token in (TemplateService._normalize_skill_proficiencies(form_data) or "").split(",")
            if token and token.strip()
        }
        if not selected_proficient_skills:
            return ""

        expertise_skills = []
        for entry in TemplateService._safe_parse_json_list(form_data.get("feat_choices")):
            if not isinstance(entry, dict):
                continue
            if str(entry.get("choice_type") or "").strip() != "expertise":
                continue
            skill_id = str(entry.get("value") or "").strip()
            if not skill_id:
                continue
            if skill_id in selected_proficient_skills and skill_id not in expertise_skills:
                expertise_skills.append(skill_id)

        return ", ".join(expertise_skills)

    @staticmethod
    def _safe_parse_json_list(raw_value):
        if not raw_value:
            return []
        try:
            data = json.loads(raw_value)
        except Exception:
            return []
        return data if isinstance(data, list) else []

    @classmethod
    def _normalize_background_ability_distribution(cls, raw_distribution):
        normalized = {}
        if not isinstance(raw_distribution, dict):
            return normalized

        for raw_key, raw_value in raw_distribution.items():
            if raw_key is None:
                continue
            key = str(raw_key).strip().lower()
            key = cls.ABILITY_ALIASES.get(key, key)
            if key not in cls.CANONICAL_ABILITIES:
                continue
            try:
                value = int(raw_value)
            except (TypeError, ValueError):
                continue
            if value <= 0:
                continue
            normalized[key] = normalized.get(key, 0) + value
        return normalized

    @classmethod
    def _validate_guided_builder_constraints(cls, form_data):
        service = get_character_builder_service()
        logger = current_app.logger if has_app_context() else logging.getLogger(__name__)
        payload_debug = form_data.to_dict(flat=False) if hasattr(form_data, "to_dict") else dict(form_data or {})
        logger.info(
            "Origin bonuses raw payload: %s",
            payload_debug.get("background_ability_bonus_allocations_json"),
        )
        logger.info("Origin bonuses full payload: %s", payload_debug)
        state = {
            "class_id": form_data.get("character_class") or None,
            "background_id": form_data.get("background_choice") or None,
            "species_id": form_data.get("race") or None,
            "language_ids": [token for token in [form_data.get("language_2"), form_data.get("language_3")] if token],
            "selected_origin_feat_id": None,
        }
        feat_choices = cls._safe_parse_json_list(form_data.get("feat_choices"))
        for entry in feat_choices:
            if isinstance(entry, dict) and entry.get("choice_type") == "origin_feat":
                state["selected_origin_feat_id"] = entry.get("value")
                break

        ability_payload = service.get_ability_score_payload(state)
        allowed_abilities = set(ability_payload.get("allowed_abilities", []))
        legacy_distribution = {}
        for field in ["force", "dexterite", "constitution", "intelligence", "sagesse", "charisme"]:
            try:
                legacy_distribution[field] = int(form_data.get(f"{field}_bg_bonus", 0) or 0)
            except Exception:
                legacy_distribution[field] = 0
        positive_distribution = cls._normalize_background_ability_distribution(legacy_distribution)

        allocations = cls._safe_parse_json_list(form_data.get("background_ability_bonus_allocations_json"))
        allocation_distribution_raw = {}
        for entry in allocations:
            if not isinstance(entry, dict):
                continue
            ability = str(entry.get("ability") or "").strip().lower()
            try:
                bonus = int(entry.get("bonus", 0) or 0)
            except Exception:
                continue
            if bonus <= 0:
                continue
            allocation_distribution_raw[ability] = allocation_distribution_raw.get(ability, 0) + bonus
        allocation_distribution = cls._normalize_background_ability_distribution(allocation_distribution_raw)
        if allocation_distribution:
            positive_distribution = allocation_distribution

        selected_mode = str(form_data.get("background_ability_bonus_mode") or "").strip().lower()
        option = "A" if selected_mode in {"2-1", "+2/+1", "increase_one_by_2_and_one_by_1"} else "B"
        logger.info("Origin bonuses chosen option: %s", option)
        logger.info(
            "Origin bonuses chosen abilities: %s",
            sorted(positive_distribution.keys()),
        )
        logger.info("Origin bonuses normalized distribution: %s", positive_distribution)

        total_bonus = sum(positive_distribution.values())
        if allowed_abilities:
            illegal = [key for key in positive_distribution if key not in allowed_abilities]
            if illegal:
                logger.warning(
                    "Origin bonus validator reject reason: illegal abilities %s (allowed=%s)",
                    illegal,
                    sorted(allowed_abilities),
                )
                raise ValueError(f"Bonus d’origine illégal: {', '.join(illegal)} hors capacités autorisées.")
            sorted_bonuses = sorted(positive_distribution.values(), reverse=True)
            is_plus_two_plus_one = sorted_bonuses == [2, 1]
            is_plus_one_three_times = sorted_bonuses == [1, 1, 1]
            if total_bonus != 3 or not (is_plus_two_plus_one or is_plus_one_three_times):
                logger.warning(
                    "Origin bonus validator reject reason: invalid distribution=%s (total=%s, sorted=%s)",
                    positive_distribution,
                    total_bonus,
                    sorted_bonuses,
                )
                raise ValueError("Les bonus d’origine doivent suivre la règle +2/+1 ou +1/+1/+1.")

        selected_by_scope_and_choice_id = {
            "class": {},
            "background": {},
            "species": {},
            "feat": {},
        }
        for entry in feat_choices:
            if isinstance(entry, dict):
                scope = str(entry.get("scope") or "").strip().lower()
                if scope == "spell":
                    scope = "class"
                elif scope.startswith("feat_"):
                    scope = "feat"
                if scope not in selected_by_scope_and_choice_id:
                    continue
                choice_id = str(entry.get("choice_id") or "")
                value = str(entry.get("value") or "")
                if not choice_id or not value:
                    continue
                selected_values = selected_by_scope_and_choice_id[scope].setdefault(choice_id, [])
                if value not in selected_values:
                    selected_values.append(value)

        skill_tokens = [token.strip() for token in (cls._normalize_skill_proficiencies(form_data) or "").split(",") if token.strip()]
        spell_tokens = [token.strip() for token in (form_data.get("selected_level_1_spells") or "").split(",") if token.strip()]
        cantrip_tokens = [token.strip() for token in (form_data.get("selected_cantrips") or "").split(",") if token.strip()]
        selected_spells_by_choice = cls._extract_selected_spells_by_choice(form_data)
        language_tokens = [token for token in [form_data.get("language_2"), form_data.get("language_3")] if token]

        def _validate_required_choices(payload, scope):
            scoped_choices = selected_by_scope_and_choice_id.get(scope, {})
            for choice in payload.get("required_choices", []) if isinstance(payload, dict) else []:
                if not isinstance(choice, dict) or not choice.get("required", True):
                    continue
                choice_id = str(choice.get("id") or "")
                choose = int(choice.get("choose", 1))
                choice_type = choice.get("type")
                if choice_type == "skill_proficiency":
                    count = (
                        len(scoped_choices.get(choice_id, []))
                        if choice_id
                        else len(skill_tokens)
                    )
                elif choice_type == "spell":
                    count = len(selected_spells_by_choice.get(choice_id, [])) if selected_spells_by_choice else len(cantrip_tokens) + len(spell_tokens)
                elif choice_type == "language":
                    # Les choix de langue attachés à une règle (classe/background/espèce/don)
                    # doivent être validés via leur choice_id dédié et non via le pool global
                    # de langues d'origine (language_2/language_3).
                    #
                    # Fallback legacy: si aucun choice_id n'est présent, on conserve
                    # l'ancien comptage basé sur les langues globales.
                    count = (
                        len(scoped_choices.get(choice_id, []))
                        if choice_id
                        else len(language_tokens)
                    )
                else:
                    count = len(scoped_choices.get(choice_id, []))
                if count != choose:
                    raise ValueError(f"Choix requis incomplet ({choice_id}): {count}/{choose}.")

        _validate_required_choices(
            service.get_class_payload(state["class_id"], state) if state["class_id"] else {},
            "class",
        )
        _validate_required_choices(
            service.get_background_payload(state["background_id"], state) if state["background_id"] else {},
            "background",
        )
        _validate_required_choices(
            service.get_species_payload(state["species_id"], state) if state["species_id"] else {},
            "species",
        )

        if state["background_id"]:
            background_payload = service.get_background_payload(state["background_id"], state)
            for choice in background_payload.get("origin_feat_payload", {}).get("required_choices", []):
                choice_id = str(choice.get("id") or "")
                choose = int(choice.get("choose", 1))
                if len(selected_by_scope_and_choice_id.get("feat", {}).get(choice_id, [])) != choose:
                    raise ValueError(f"Sous-choix de don d’origine incomplet ({choice_id}).")

        if state["species_id"] and state["selected_origin_feat_id"]:
            feat_payload = service.get_feat_payload(state["selected_origin_feat_id"], state)
            for choice in feat_payload.get("required_choices", []):
                choice_id = str(choice.get("id") or "")
                choose = int(choice.get("choose", 1))
                if len(selected_by_scope_and_choice_id.get("feat", {}).get(choice_id, [])) != choose:
                    raise ValueError(f"Sous-choix de don bonus d’espèce incomplet ({choice_id}).")

        class_payload = service.get_class_payload(state["class_id"], state) if state["class_id"] else {}
        background_payload = service.get_background_payload(state["background_id"], state) if state["background_id"] else {}
        needs_equipment = bool(class_payload.get("equipment_options")) or bool(background_payload.get("equipment_options"))
        if needs_equipment and not (form_data.get("equipment") or "").strip():
            raise ValueError("Sélection d’équipement incomplète.")

    @staticmethod
    def split_builder_equipment(equipment_value):
        """Reconstitue les champs du funnel a partir de la chaine equipement stockee."""
        parsed = {
            "equipment": "",
            "weapon_loadout": "",
            "ranged_weapon_loadout": "",
            "armor_loadout": "",
            "inventory_items": "",
            "skill_proficiencies": "",
            "expertise_skills": "",
            "tool_proficiencies": "",
            "spellbook_notes": "",
        }
        if not equipment_value:
            return parsed

        mapping = {
            "Equipement principal:": "equipment",
            "Armes equipees:": "weapon_loadout",
            "Arme de corps a corps equipee:": "weapon_loadout",
            "Arme a distance equipee:": "ranged_weapon_loadout",
            "Armure/Bouclier:": "armor_loadout",
            "Inventaire:": "inventory_items",
            "Competences maitrisees:": "skill_proficiencies",
            "Expertises:": "expertise_skills",
            "Outils maitrises:": "tool_proficiencies",
            "Sorts/Aptitudes:": "spellbook_notes",
        }

        chunks = [chunk.strip() for chunk in equipment_value.split("|") if chunk.strip()]
        for chunk in chunks:
            for prefix, key in mapping.items():
                if chunk.startswith(prefix):
                    parsed[key] = chunk.replace(prefix, "", 1).strip()
                    break
            else:
                if not parsed["equipment"]:
                    parsed["equipment"] = chunk
        return parsed

    @staticmethod
    def _compose_background_payload(form_data):
        """Conserve le background mecanique + le backstory libre dans un seul champ DB."""
        background_choice = (form_data.get('background_choice') or form_data.get('background_story') or '').strip()
        backstory_text = (form_data.get('backstory_text') or '').strip()
        if not background_choice and not backstory_text:
            return None
        if not background_choice:
            return backstory_text
        if not backstory_text:
            return background_choice
        return f"{background_choice}\n\n{backstory_text}"

    @staticmethod
    def split_background_payload(background_story):
        """Separer background choisi et backstory libre pour pre-remplir l'edition."""
        if not background_story:
            return {"background_choice": "", "backstory_text": ""}

        parts = [part.strip() for part in background_story.split("\n\n", 1)]
        if len(parts) == 1:
            return {"background_choice": parts[0], "backstory_text": ""}
        return {"background_choice": parts[0], "backstory_text": parts[1]}

    @staticmethod
    def create_character_template(form_data, files, upload_folder, current_user_id=None, campaign_id=None):
        """Créer un nouveau template de personnage"""
        payload_debug = form_data.to_dict(flat=False) if hasattr(form_data, "to_dict") else dict(form_data or {})
        current_app.logger.info("CREATE_CHARACTER raw form payload=%s", payload_debug)
        current_app.logger.info("CREATE_CHARACTER files=%s", list(files.keys()) if files else [])

        image = files.get("image")
        pdf = files.get("pdf")
        filename = None
        pdf_filename = None

        # Gestion de l'image
        if image and image.filename != "" and allowed_file(image.filename):
            filename = TemplateService._save_uploaded_file(image, upload_folder)

        # Gestion du PDF
        if pdf and pdf.filename != "" and pdf.filename.lower().endswith(".pdf"):
            pdf_filename = TemplateService._save_uploaded_file(pdf, upload_folder)

        # ✅ CORRECTION : Récupérer l'utilisateur connecté
        from flask import session
        current_user_id = current_user_id or session.get('user_id')
        if not current_user_id:
            raise ValueError("Aucun utilisateur connecté")
        current_user = User.query.get(current_user_id)

        resolved_campaign_id = campaign_id if campaign_id is not None else form_data.get('campaign_id')

        current_app.logger.info("CREATE_CHARACTER STEP normalize_builder_state start")
        normalized_state = {
            "class_id": form_data.get("character_class") or None,
            "background_id": form_data.get("background_choice") or None,
            "species_id": form_data.get("race") or None,
            "level": int(form_data.get("level", 1) or 1),
            "language_ids": [token for token in [form_data.get("language_2"), form_data.get("language_3")] if token],
            "selected_equipment_ids": [token for token in getattr(form_data, "getlist", lambda _k: [])("selected_equipment_ids") if token],
            "selected_class_choice_ids": TemplateService._safe_parse_json_list(form_data.get("feat_choices")),
        }
        current_app.logger.info("CREATE_CHARACTER STEP normalized_state=%s", normalized_state)

        current_app.logger.info("CREATE_CHARACTER STEP build_character_domain_payload start")
        resolved_character = resolve_character_creation(form_data)
        current_app.logger.info(
            "CREATE_CHARACTER STEP final_ability_scores=%s",
            {
                "force": resolved_character.get("force"),
                "dexterite": resolved_character.get("dexterite"),
                "constitution": resolved_character.get("constitution"),
                "intelligence": resolved_character.get("intelligence"),
                "sagesse": resolved_character.get("sagesse"),
                "charisme": resolved_character.get("charisme"),
            },
        )
        TemplateService._apply_armor_loadout_to_ac_base(resolved_character, form_data.get('armor_loadout'))
        normalized_skill_proficiencies = TemplateService._normalize_skill_proficiencies(form_data, resolved_character=resolved_character)
        current_app.logger.info("CREATE_CHARACTER STEP skill_proficiencies=%s", normalized_skill_proficiencies)
        current_app.logger.info("CREATE_CHARACTER STEP expertise=%s", TemplateService._extract_expertise_skills(form_data))
        TemplateService._validate_skill_proficiencies_limit(
            resolved_character.get('character_class') or form_data.get('character_class'),
            normalized_skill_proficiencies,
            form_data=form_data,
        )
        spellcasting_ability, spell_save_dc, spell_attack_bonus = TemplateService._derive_spellcasting_stats(
            resolved_character.get('character_class') or form_data.get('character_class'),
            resolved_character.get('level') or form_data.get('level'),
            resolved_character,
        )
        selected_cantrips = TemplateService._normalize_selected_spells(form_data, 'selected_cantrips')
        selected_level_1_spells = TemplateService._normalize_selected_spells(form_data, 'selected_level_1_spells')
        uses_choice_based_spell_selection = TemplateService._uses_choice_based_spell_selection(form_data)
        TemplateService._validate_equipment_mastery(
            resolved_character.get('character_class') or form_data.get('character_class'),
            form_data.get('weapon_loadout'),
            form_data.get('armor_loadout'),
        )
        if not uses_choice_based_spell_selection:
            cantrip_catalog = get_cantrips()
            level_one_catalog = get_spells_for_level(1)
            selected_cantrips = TemplateService._canonicalize_selected_spells(selected_cantrips, cantrip_catalog)
            selected_level_1_spells = TemplateService._canonicalize_selected_spells(selected_level_1_spells, level_one_catalog)
            TemplateService._validate_selected_spells_exist(selected_cantrips, cantrip_catalog, "Sorts mineurs")
            TemplateService._validate_selected_spells_exist(selected_level_1_spells, level_one_catalog, "Sorts de niveau 1")
            TemplateService._validate_spell_selection_rules(
                resolved_character.get('character_class') or form_data.get('character_class'),
                selected_cantrips,
                selected_level_1_spells,
                cantrip_catalog,
                level_one_catalog,
            )
        selected_languages = [
            TemplateService._normalize_language_label(form_data.get('language_1')),
            TemplateService._normalize_language_label(form_data.get('language_2')),
            TemplateService._normalize_language_label(form_data.get('language_3')),
        ]
        selected_languages = [language for language in selected_languages if language]
        if len(set(selected_languages)) < 3 or 'Commun' not in selected_languages:
            raise ValueError("Les langues doivent inclure Commun et 2 langues distinctes.")
        TemplateService._validate_guided_builder_constraints(form_data)

        identity_bits = []
        if form_data.get('genre'):
            identity_bits.append(f"Genre: {form_data.get('genre')}")
        if form_data.get('alignment'):
            identity_bits.append(f"Alignement: {form_data.get('alignment')}")
        if form_data.get('weight'):
            identity_bits.append(f"Poids: {form_data.get('weight')}")
        if selected_languages:
            identity_bits.append(f"Langues: {', '.join(selected_languages)}")

        shared_notes = form_data.get('notes', '')
        if identity_bits:
            identity_notes = "\n".join(identity_bits)
            shared_notes = f"{identity_notes}\n{shared_notes}".strip()

        template = CharacterTemplate(
            # ✅ AJOUT : Champs de sécurité
            owner_id=current_user_id,
            campaign_id=resolved_campaign_id,
            character_type=form_data.get('character_type', 'PJ'),
            is_shared=form_data.get('is_shared', False),
            is_public=bool(form_data.get('is_public', False)),  # ✅ CORRECTION : Forcer le booléen
            visibility_level=form_data.get('visibility_level', 'private'),

            # Données existantes
            name=form_data['name'],
            race=resolved_character['race'],
            character_class=resolved_character['character_class'],
            level=resolved_character['level'],
            hp_max=resolved_character['hp_max'],
            hp_current=resolved_character['hp_max'],
            ac_base=resolved_character['ac_base'],
            ac_bonus=0,
            initiative_bonus=resolved_character['initiative_bonus'],

            # Caractéristiques
            force=resolved_character['force'],
            dexterite=resolved_character['dexterite'],
            constitution=resolved_character['constitution'],
            intelligence=resolved_character['intelligence'],
            sagesse=resolved_character['sagesse'],
            charisme=resolved_character['charisme'],

            # Maîtrises de sauvegarde
            maitrise_force=resolved_character['maitrise_force'],
            maitrise_dexterite=resolved_character['maitrise_dexterite'],
            maitrise_constitution=resolved_character['maitrise_constitution'],
            maitrise_intelligence=resolved_character['maitrise_intelligence'],
            maitrise_sagesse=resolved_character['maitrise_sagesse'],
            maitrise_charisme=resolved_character['maitrise_charisme'],

            image_filename=filename,
            pdf_filename=pdf_filename,
            notes=shared_notes,
            player_private_notes=form_data.get('player_private_notes', ''),
            first_name=form_data.get('first_name') or None,
            gender=form_data.get('genre') or None,
            player_name=current_user.username if current_user else None,
            campaign_name=form_data.get('campaign_name') or None,
            alignment=form_data.get('alignment') or None,
            languages=', '.join(selected_languages) if selected_languages else None,
            height=form_data.get('height') or None,
            weight=form_data.get('weight') or None,
            eyes=form_data.get('eyes') or None,
            skin=form_data.get('skin') or None,
            hair=form_data.get('hair') or None,
            equipment=TemplateService._compose_builder_equipment(form_data),
            skill_proficiencies=normalized_skill_proficiencies,
            age=int(form_data.get('age')) if form_data.get('age') else None,
            character_appearance=form_data.get('character_appearance') or None,
            allies_organizations=form_data.get('allies_organizations') or None,
            additional_features_traits=form_data.get('additional_features_traits') or None,
            treasure=form_data.get('treasure') or None,
            symbol_name=form_data.get('symbol_name') or None,
            personality_traits=form_data.get('personality_traits') or None,
            ideals=form_data.get('ideals') or None,
            bonds=form_data.get('bonds') or None,
            flaws=form_data.get('flaws') or None,
            inspiration=bool(form_data.get('inspiration')),
            spellcasting_class=resolved_character.get('character_class') or form_data.get('spellcasting_class') or None,
            spellcasting_ability=spellcasting_ability,
            spell_save_dc=spell_save_dc,
            spell_attack_bonus=spell_attack_bonus,
            selected_cantrips=selected_cantrips,
            selected_level_1_spells=selected_level_1_spells,
            background_story=TemplateService._compose_background_payload(form_data),
            current_xp=int(form_data.get('current_xp', 0))
        )

        db.session.add(template)
        db.session.flush()

        current_app.logger.info(
            "CREATE_CHARACTER PERSIST character_payload=%s",
            {
                "name": template.name,
                "race": template.race,
                "character_class": template.character_class,
                "level": template.level,
                "equipment": template.equipment,
                "skill_proficiencies": template.skill_proficiencies,
                "languages": template.languages,
            },
        )

        if resolved_campaign_id:
            from app.models.campaign import Campaign
            campaign = Campaign.query.get(int(resolved_campaign_id))
            if campaign and campaign not in template.campaigns:
                template.campaigns.append(campaign)

        # Le funnel guide devient la source unique: chaque creation persiste un PDF officiel.
        template.pdf_filename = CharacterSheetPdfService.generate(template, upload_folder)

        db.session.commit()

        if template.character_type == "PJ" and template.campaign:
            if template.owner_id == template.campaign.mj_id:
                NotificationService.create_campaign_notification(
                    template.campaign,
                    "Nouveau PJ du MJ",
                    f'Le MJ a ajouté le PJ "{template.name}" à la campagne "{template.campaign.name}".',
                    kind='shared_pj_added',
                )
            else:
                NotificationService.create_notification(
                    template.campaign.mj_id,
                    "Nouveau PJ ajouté",
                    f'Un joueur a ajouté le PJ "{template.name}" à la campagne "{template.campaign.name}".',
                    kind='player_pj_added',
                    campaign_id=template.campaign_id,
                )

        return template

    @staticmethod
    def build_transient_character_template(form_data, current_user=None):
        """Construit un personnage non persiste pour les apercus (ex: generation PDF)."""
        resolved_character = resolve_character_creation(form_data)
        TemplateService._apply_armor_loadout_to_ac_base(resolved_character, form_data.get('armor_loadout'))
        normalized_skill_proficiencies = TemplateService._normalize_skill_proficiencies(form_data, resolved_character=resolved_character)
        TemplateService._validate_skill_proficiencies_limit(
            resolved_character.get('character_class') or form_data.get('character_class'),
            normalized_skill_proficiencies,
            form_data=form_data,
        )

        spellcasting_ability, spell_save_dc, spell_attack_bonus = TemplateService._derive_spellcasting_stats(
            resolved_character.get('character_class') or form_data.get('character_class'),
            resolved_character.get('level') or form_data.get('level'),
            resolved_character,
        )
        selected_cantrips = TemplateService._normalize_selected_spells(form_data, 'selected_cantrips')
        selected_level_1_spells = TemplateService._normalize_selected_spells(form_data, 'selected_level_1_spells')
        uses_choice_based_spell_selection = TemplateService._uses_choice_based_spell_selection(form_data)
        TemplateService._validate_equipment_mastery(
            resolved_character.get('character_class') or form_data.get('character_class'),
            form_data.get('weapon_loadout'),
            form_data.get('armor_loadout'),
        )
        if not uses_choice_based_spell_selection:
            cantrip_catalog = get_cantrips()
            level_one_catalog = get_spells_for_level(1)
            selected_cantrips = TemplateService._canonicalize_selected_spells(selected_cantrips, cantrip_catalog)
            selected_level_1_spells = TemplateService._canonicalize_selected_spells(selected_level_1_spells, level_one_catalog)
            TemplateService._validate_selected_spells_exist(selected_cantrips, cantrip_catalog, "Sorts mineurs")
            TemplateService._validate_selected_spells_exist(selected_level_1_spells, level_one_catalog, "Sorts de niveau 1")
            TemplateService._validate_spell_selection_rules(
                resolved_character.get('character_class') or form_data.get('character_class'),
                selected_cantrips,
                selected_level_1_spells,
                cantrip_catalog,
                level_one_catalog,
            )
        selected_languages = [
            TemplateService._normalize_language_label(form_data.get('language_1')),
            TemplateService._normalize_language_label(form_data.get('language_2')),
            TemplateService._normalize_language_label(form_data.get('language_3')),
        ]
        selected_languages = [language for language in selected_languages if language]
        if len(set(selected_languages)) < 3 or 'Commun' not in selected_languages:
            raise ValueError("Les langues doivent inclure Commun et 2 langues distinctes.")
        TemplateService._validate_guided_builder_constraints(form_data)

        identity_bits = []
        if form_data.get('genre'):
            identity_bits.append(f"Genre: {form_data.get('genre')}")
        if form_data.get('alignment'):
            identity_bits.append(f"Alignement: {form_data.get('alignment')}")
        if form_data.get('weight'):
            identity_bits.append(f"Poids: {form_data.get('weight')}")
        if selected_languages:
            identity_bits.append(f"Langues: {', '.join(selected_languages)}")

        shared_notes = form_data.get('notes', '')
        if identity_bits:
            identity_notes = "\n".join(identity_bits)
            shared_notes = f"{identity_notes}\n{shared_notes}".strip()

        transient_character = CharacterTemplate(
            character_type=form_data.get('character_type', 'PJ'),
            is_shared=form_data.get('is_shared', False),
            is_public=bool(form_data.get('is_public', False)),
            visibility_level=form_data.get('visibility_level', 'private'),
            name=form_data.get('name', 'Personnage'),
            race=resolved_character['race'],
            character_class=resolved_character['character_class'],
            level=resolved_character['level'],
            hp_max=resolved_character['hp_max'],
            hp_current=resolved_character['hp_max'],
            ac_base=resolved_character['ac_base'],
            ac_bonus=0,
            initiative_bonus=resolved_character['initiative_bonus'],
            force=resolved_character['force'],
            dexterite=resolved_character['dexterite'],
            constitution=resolved_character['constitution'],
            intelligence=resolved_character['intelligence'],
            sagesse=resolved_character['sagesse'],
            charisme=resolved_character['charisme'],
            maitrise_force=resolved_character['maitrise_force'],
            maitrise_dexterite=resolved_character['maitrise_dexterite'],
            maitrise_constitution=resolved_character['maitrise_constitution'],
            maitrise_intelligence=resolved_character['maitrise_intelligence'],
            maitrise_sagesse=resolved_character['maitrise_sagesse'],
            maitrise_charisme=resolved_character['maitrise_charisme'],
            notes=shared_notes,
            player_private_notes=form_data.get('player_private_notes', ''),
            first_name=form_data.get('first_name') or None,
            gender=form_data.get('genre') or None,
            player_name=current_user.username if current_user else None,
            campaign_name=form_data.get('campaign_name') or None,
            alignment=form_data.get('alignment') or None,
            languages=', '.join(selected_languages) if selected_languages else None,
            height=form_data.get('height') or None,
            weight=form_data.get('weight') or None,
            eyes=form_data.get('eyes') or None,
            skin=form_data.get('skin') or None,
            hair=form_data.get('hair') or None,
            equipment=TemplateService._compose_builder_equipment(form_data),
            skill_proficiencies=normalized_skill_proficiencies,
            age=int(form_data.get('age')) if form_data.get('age') else None,
            character_appearance=form_data.get('character_appearance') or None,
            allies_organizations=form_data.get('allies_organizations') or None,
            additional_features_traits=form_data.get('additional_features_traits') or None,
            treasure=form_data.get('treasure') or None,
            symbol_name=form_data.get('symbol_name') or None,
            spellcasting_class=resolved_character.get('character_class') or form_data.get('spellcasting_class') or None,
            spellcasting_ability=spellcasting_ability,
            spell_save_dc=spell_save_dc,
            spell_attack_bonus=spell_attack_bonus,
            selected_cantrips=selected_cantrips,
            selected_level_1_spells=selected_level_1_spells,
            background_story=TemplateService._compose_background_payload(form_data),
            current_xp=int(form_data.get('current_xp', 0)),
            personality_traits=form_data.get('personality_traits') or None,
            ideals=form_data.get('ideals') or None,
            bonds=form_data.get('bonds') or None,
            flaws=form_data.get('flaws') or None,
            inspiration=bool(form_data.get('inspiration')),
        )
        return transient_character

    @staticmethod
    def generate_character_sheet_preview_pdf(form_data, upload_folder, current_user=None):
        """Genere un PDF de previsualisation sans persister le personnage."""
        transient_character = TemplateService.build_transient_character_template(form_data, current_user=current_user)
        return CharacterSheetPdfService.generate(transient_character, upload_folder)

    @staticmethod
    def update_character_template(template_id, form_data, files, upload_folder):
        """Mettre à jour un template de personnage"""
        template = CharacterTemplate.query.get_or_404(template_id)
        if not (form_data.get('name') or '').strip():
            raise ValueError("Le nom du personnage est obligatoire.")

        # Limiter strictement l'édition aux informations d'identité, d'apparence, de média et de visibilité.
        template.name = form_data.get('name', '').strip()
        template.player_name = form_data.get('player_name') or None
        template.campaign_name = form_data.get('campaign_name') or None
        template.gender = form_data.get('gender') or form_data.get('genre') or None
        template.alignment = form_data.get('alignment') or None
        template.languages = form_data.get('languages') or None
        template.age = int(form_data.get('age')) if form_data.get('age') else None

        template.height = form_data.get('height') or None
        template.weight = form_data.get('weight') or None
        template.eyes = form_data.get('eyes') or None
        template.skin = form_data.get('skin') or None
        template.hair = form_data.get('hair') or None
        template.character_appearance = form_data.get('character_appearance') or None

        template.is_public = bool(form_data.get('is_public', False))
        template.visibility_level = form_data.get('visibility_level', 'private')

        # Gestion des fichiers
        image = files.get("image")
        if image and image.filename != "" and allowed_file(image.filename):
            filename = TemplateService._save_uploaded_file(image, upload_folder)
            template.image_filename = filename

        pdf = files.get("pdf")
        if pdf and pdf.filename != "" and pdf.filename.lower().endswith(".pdf"):
            pdf_filename = TemplateService._save_uploaded_file(pdf, upload_folder)
            template.pdf_filename = pdf_filename

        db.session.commit()

        if template.character_type == "PJ" and template.campaign and template.owner_id != template.campaign.mj_id:
            NotificationService.create_notification(
                template.campaign.mj_id,
                "PJ modifié",
                f'Un joueur a modifié son PJ "{template.name}" dans la campagne "{template.campaign.name}".',
                kind='player_pj_updated',
                campaign_id=template.campaign_id,
            )

        return template

    @staticmethod
    def generate_character_sheet_pdf(template_id, upload_folder):
        """Regenerer une fiche PDF officielle a partir des donnees du personnage."""
        template = CharacterTemplate.query.get_or_404(template_id)
        template.pdf_filename = CharacterSheetPdfService.generate(template, upload_folder)
        db.session.commit()
        return template

    @staticmethod
    def create_encounter_template(form_data, owner_id):
        """Créer un nouveau template de rencontre"""
        combatants_data = []

        # Récupérer les données depuis le formulaire
        names = form_data.getlist('combatant_name')
        types = form_data.getlist('combatant_type')
        hps = form_data.getlist('combatant_hp')
        acs = form_data.getlist('combatant_ac')
        initiatives = form_data.getlist('combatant_initiative')

        for i in range(len(names)):
            if names[i]:  # si nom non vide
                combatants_data.append({
                    'name': names[i],
                    'type': types[i],
                    'hp_max': int(hps[i]),
                    'ac_base': int(acs[i]),
                    'initiative': int(initiatives[i])
                })

        template = EncounterTemplate(
            owner_id=owner_id,
            name=form_data['name'],
            description=form_data.get('description', ''),
            difficulty=form_data['difficulty'],
            combatants_json=json.dumps(combatants_data)
        )

        db.session.add(template)
        db.session.commit()

        return template

    @staticmethod
    def add_character_template_to_combat(combat_id, template_id, initiative):
        """Ajouter un template de personnage à un combat"""
        template = CharacterTemplate.query.get_or_404(template_id)

        combatant = Combatant(
            combat_id=combat_id,
            character_template_id=template.id,
            name=template.name,
            type="PJ",
            hp_max=template.hp_max,
            hp_current=template.hp_current_effective,
            ac_base=template.ac_base,
            ac_bonus=0,
            initiative=initiative,
            notes=template.image_filename  # Pour stocker le nom de l'image
        )

        db.session.add(combatant)
        db.session.commit()

        return combatant

    @staticmethod
    def load_encounter_template(combat_id, encounter_id):
        """Charger un template de rencontre dans un combat"""
        encounter = EncounterTemplate.query.get_or_404(encounter_id)
        combatants_data = json.loads(encounter.combatants_json)

        created_combatants = []
        for data in combatants_data:
            combatant = Combatant(
                name=data['name'],
                type=data['type'],
                hp_max=data['hp_max'],
                hp_current=data['hp_max'],
                initiative=data['initiative'],
                ac_base=data['ac_base'],
                ac_bonus=0,
                conditions="",
                combat_id=combat_id
            )

            db.session.add(combatant)
            created_combatants.append(combatant)

        db.session.commit()

        return created_combatants

    @staticmethod
    def add_monster_template_to_combat(combat_id, template_name, quantity, manual_initiative=None, monster_image_filename=None):
        """Ajouter des monstres depuis les templates prédéfinis"""
        template = MONSTER_TEMPLATES.get(template_name)

        if not template:
            return []

        created_combatants = []
        default_image_filename = template.get("image")
        selected_image_filename = monster_image_filename or default_image_filename
        display_name = template.get("display_name", template_name)

        for i in range(quantity):
            # Initiative manuelle ou celle du template
            if manual_initiative and manual_initiative.strip() != "":
                initiative_value = int(manual_initiative)
            else:
                initiative_value = template["initiative"]

            combatant = Combatant(
                name=f"{display_name} {i + 1}" if quantity > 1 else display_name,
                type=template["type"],
                hp_max=template["hp"],
                hp_current=template["hp"],
                initiative=initiative_value,
                ac_base=template["ac"],
                ac_bonus=0,
                conditions="",
                combat_id=combat_id,
                notes=selected_image_filename
            )

            db.session.add(combatant)
            created_combatants.append(combatant)

        db.session.commit()

        return created_combatants

    @staticmethod
    def delete_character_template(template_id):
        """Supprimer un template de personnage"""
        template = CharacterTemplate.query.get_or_404(template_id)
        campaign = template.campaign
        template_name = template.name
        character_type = template.character_type

        db.session.delete(template)
        db.session.commit()

        if character_type == "PJ" and campaign:
            NotificationService.create_notification(
                campaign.mj_id,
                "PJ supprimé",
                f'Un joueur a supprimé son PJ "{template_name}" de la campagne "{campaign.name}".',
                kind='player_pj_deleted',
                campaign_id=campaign.id,
            )

        return True

    @staticmethod
    def delete_encounter_template(template_id):
        """Supprimer un template de rencontre"""
        template = EncounterTemplate.query.get_or_404(template_id)
        db.session.delete(template)
        db.session.commit()

        return True

    @staticmethod
    def get_character_combat_count(character_name):
        """Obtenir le nombre de combats joués par un personnage"""
        return Combatant.query.filter_by(name=character_name).count()

    @staticmethod
    def export_templates(owner_id=None):
        """Exporter tous les templates en JSON"""
        characters_query = CharacterTemplate.query
        encounters_query = EncounterTemplate.query

        if owner_id is not None:
            characters_query = characters_query.filter_by(owner_id=owner_id)
            encounters_query = encounters_query.filter_by(owner_id=owner_id)

        characters = characters_query.all()
        encounters = encounters_query.all()

        export_data = {
            'characters': [{
                'name': c.name,
                'character_class': c.character_class,
                'level': c.level,
                'hp_max': c.hp_max,
                'ac_base': c.ac_base,
                'initiative_bonus': c.initiative_bonus,
                'notes': c.notes
            } for c in characters],

            'encounters': [{
                'name': e.name,
                'description': e.description,
                'difficulty': e.difficulty,
                'combatants_json': e.combatants_json
            } for e in encounters]
        }

        return export_data
