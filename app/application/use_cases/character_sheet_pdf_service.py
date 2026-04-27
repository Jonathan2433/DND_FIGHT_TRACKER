"""Generation de fiche PDF DnD5 a partir des donnees personnage."""
from __future__ import annotations

import re
import json
import os
import logging
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter
from pypdf.generic import BooleanObject, NameObject, TextStringObject
from app.utils.dnd5_rules import SPECIES_RULES


logger = logging.getLogger(__name__)


class CharacterSheetPdfService:
    """Construit un PDF de fiche personnage depuis le template officiel fillable."""

    TEMPLATE_FILENAME = "5E_CharacterSheet_Fillable.pdf"
    LEGACY_TEMPLATE_FILENAMES = (
        "Feuille_de_personnage_Dungeons__Dragons_-_DD_5_2.pdf",
        "Feuille_de_personnage_Dungeons__Dragons_-_DD_5_1.pdf",
    )
    STATIC_UPLOADS_DIR = Path(__file__).resolve().parents[3] / "static" / "uploads"

    # Mapping metier -> noms techniques connus des champs PDF.
    # Le premier nom correspond au template officiel 5E_CharacterSheet_Fillable.pdf.
    FIELD_ALIASES: dict[str, tuple[str, ...]] = {
        "character_name": ("CharacterName", "Character Name", "CharName", "CharacterName 2"),
        "class_level": ("ClassLevel", "Class & Level", "ClassLevel1"),
        "background": ("Background",),
        "character_backstory": ("Backstory", "Character Backstory", "CharacterBackstory"),
        "player_name": ("PlayerName", "Player Name"),
        "race": ("Race ", "Race"),
        "alignment": ("Alignment",),
        "experience_points": ("XP", "Experience Points", "ExperiencePoints"),
        "strength": ("STR", "Strength", "StrengthScore"),
        "strength_mod": ("STRmod", "StrengthMod", "Strength Modifier"),
        "dexterity": ("DEX", "Dexterity", "DexterityScore"),
        "dexterity_mod": ("DEXmod", "DexterityMod", "Dex Modifier"),
        "constitution": ("CON", "Constitution", "ConstitutionScore"),
        "constitution_mod": ("CONmod", "ConstitutionMod", "Con Modifier"),
        "intelligence": ("INT", "Intelligence", "IntelligenceScore"),
        "intelligence_mod": ("INTmod", "IntelligenceMod", "Int Modifier"),
        "wisdom": ("WIS", "Wisdom", "WisdomScore"),
        "wisdom_mod": ("WISmod", "WisdomMod", "Wis Modifier"),
        "charisma": ("CHA", "Charisma", "CharismaScore"),
        "charisma_mod": ("CHamod", "CHAmod", "CharismaMod", "Cha Modifier"),
        "proficiency_bonus": ("ProfBonus", "Proficiency Bonus", "PB"),
        "armor_class": ("AC", "Armor Class"),
        "armor_class_badge": ("AP", "ArmorClass2", "Armor Class 2"),
        "initiative": ("Initiative",),
        "speed": ("Speed",),
        "hp_max": ("HPMax", "HP Max", "Hit Point Maximum"),
        "hp_current": ("HPCurrent", "Current HP", "Current Hit Points"),
        "temp_hp": ("HPTemp", "Temp HP", "Temporary Hit Points"),
        "languages": ("Languages",),
        "proficiencies_languages": ("ProficienciesLang", "Proficiencies & Languages", "Proficiencies and Languages"),
        "equipment": ("Equipment", "EquipmentNotes"),
        "features_traits": ("Features and Traits", "FeaturesTraits", "Features and Traits 1"),
        "passive_wisdom": ("Passive", "Passive Wisdom (Perception)"),
        "proficiency_checkbox": ("ProfCheckbox", "Inspiration", "Inspiration Checkbox"),
        "age": ("Age",),
        "height": ("Height",),
        "weight": ("Weight",),
        "eyes": ("Eyes",),
        "skin": ("Skin",),
        "hair": ("Hair",),
        "personality_traits": ("PersonalityTraits", "Personality Traits"),
        "ideals": ("Ideals",),
        "bonds": ("Bonds",),
        "flaws": ("Flaws",),
        "attacks_spellcasting": ("AttacksSpellcasting", "Attacks & Spellcasting"),
        "weapon_1_name": ("Wpn Name",),
        "weapon_1_attack_bonus": ("Wpn1 AtkBonus",),
        "weapon_1_damage_type": ("Wpn1 Damage",),
        "weapon_2_name": ("Wpn Name 2",),
        "weapon_2_attack_bonus": ("Wpn2 AtkBonus", "Wpn2 AtkBonus "),
        "weapon_2_damage_type": ("Wpn2 Damage", "Wpn2 Damage "),
        "weapon_3_name": ("Wpn Name 3",),
        "weapon_3_attack_bonus": ("Wpn3 AtkBonus", "Wpn3 AtkBonus  "),
        "weapon_3_damage_type": ("Wpn3 Damage", "Wpn3 Damage "),
        "allies_organizations": ("AlliesOrganizations", "Allies & Organizations"),
        "character_appearance": ("CharacterAppearance", "CHARACTER APPEARANCE"),
        "additional_features_traits": ("AdditionalFeatandTraits", "Additional Features and Traits"),
        "treasure": ("Treasure",),
        "symbol_name": ("FactionName", "Faction Name", "Name"),
        "spellcasting_class": ("Spellcasting Class 2", "Spellcasting Class"),
        "spellcasting_ability": ("SpellcastingAbility 2", "Spellcasting Ability"),
        "spell_save_dc": ("SpellSaveDC 2", "Spell Save DC"),
        "spell_attack_bonus": ("SpellAtkBonus 2", "Spell Attack Bonus"),
        "saving_throw_strength": ("ST Strength",),
        "saving_throw_dexterity": ("ST Dexterity",),
        "saving_throw_constitution": ("ST Constitution",),
        "saving_throw_intelligence": ("ST Intelligence",),
        "saving_throw_wisdom": ("ST Wisdom",),
        "saving_throw_charisma": ("ST Charisma",),
        "saving_throw_strength_prof": ("Check Box 11",),
        "saving_throw_dexterity_prof": ("Check Box 18",),
        "saving_throw_constitution_prof": ("Check Box 19",),
        "saving_throw_intelligence_prof": ("Check Box 20",),
        "saving_throw_wisdom_prof": ("Check Box 21",),
        "saving_throw_charisma_prof": ("Check Box 22",),
        "acrobatics": ("Acrobatics",),
        "animal_handling": ("Animal", "Animal Handling"),
        "arcana": ("Arcana",),
        "athletics": ("Athletics",),
        "deception": ("Deception ", "Deception"),
        "history": ("History ", "History"),
        "insight": ("Insight",),
        "intimidation": ("Intimidation",),
        "investigation": ("Investigation ", "Investigation"),
        "medicine": ("Medicine",),
        "nature": ("Nature",),
        "perception": ("Perception ", "Perception"),
        "performance": ("Performance",),
        "persuasion": ("Persuasion",),
        "religion": ("Religion",),
        "sleight_of_hand": ("SleightofHand", "Sleight of Hand"),
        "stealth": ("Stealth ", "Stealth"),
        "survival": ("Survival",),
        "acrobatics_prof": ("Check Box 23",),
        "animal_handling_prof": ("Check Box 24",),
        "arcana_prof": ("Check Box 25",),
        "athletics_prof": ("Check Box 26",),
        "deception_prof": ("Check Box 27",),
        "history_prof": ("Check Box 28",),
        "insight_prof": ("Check Box 29",),
        "intimidation_prof": ("Check Box 30",),
        "investigation_prof": ("Check Box 31",),
        "medicine_prof": ("Check Box 32",),
        "nature_prof": ("Check Box 33",),
        "perception_prof": ("Check Box 34",),
        "performance_prof": ("Check Box 35",),
        "persuasion_prof": ("Check Box 36",),
        "religion_prof": ("Check Box 37",),
        "sleight_of_hand_prof": ("Check Box 38",),
        "stealth_prof": ("Check Box 39",),
        "survival_prof": ("Check Box 40",),
    }

    REQUIRED_MAPPING_KEYS = ("character_name", "class_level", "race", "armor_class", "strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma")
    SKILL_TO_ABILITY = {
        "acrobatics": "dexterite",
        "animal_handling": "sagesse",
        "arcana": "intelligence",
        "athletics": "force",
        "deception": "charisme",
        "history": "intelligence",
        "insight": "sagesse",
        "intimidation": "charisme",
        "investigation": "intelligence",
        "medicine": "sagesse",
        "nature": "intelligence",
        "perception": "sagesse",
        "performance": "charisme",
        "persuasion": "charisme",
        "religion": "intelligence",
        "sleight_of_hand": "dexterite",
        "stealth": "dexterite",
        "survival": "sagesse",
    }
    WEAPON_PROFILES = {
        "epee longue": {"damage": "1d8", "damage_type": "Tranchant", "is_ranged": False, "finesse": False},
        "epee courte": {"damage": "1d6", "damage_type": "Percant", "is_ranged": False, "finesse": True},
        "dague": {"damage": "1d4", "damage_type": "Percant", "is_ranged": False, "finesse": True},
        "hachette": {"damage": "1d6", "damage_type": "Tranchant", "is_ranged": False, "finesse": False},
        "marteau leger": {"damage": "1d4", "damage_type": "Contondant", "is_ranged": False, "finesse": False},
        "lance": {"damage": "1d6", "damage_type": "Percant", "is_ranged": False, "finesse": False},
        "arc court": {"damage": "1d6", "damage_type": "Percant", "is_ranged": True, "finesse": False},
        "arc long": {"damage": "1d8", "damage_type": "Percant", "is_ranged": True, "finesse": False},
        "arbalete legere": {"damage": "1d8", "damage_type": "Percant", "is_ranged": True, "finesse": False},
        "arbalete de poing": {"damage": "1d6", "damage_type": "Percant", "is_ranged": True, "finesse": False},
    }
    DAMAGE_TYPE_FR = {
        "piercing": "Percant",
        "slashing": "Tranchant",
        "bludgeoning": "Contondant",
        "force": "Force",
        "fire": "Feu",
        "cold": "Froid",
        "lightning": "Foudre",
        "thunder": "Tonnerre",
        "acid": "Acide",
        "poison": "Poison",
        "necrotic": "Necrotique",
        "radiant": "Radiant",
        "psychic": "Psychique",
    }
    _WEAPONS_CATALOG_CACHE: list[dict[str, Any]] | None = None

    @staticmethod
    def _format_mod(value: int) -> str:
        return f"{value:+d}"

    @staticmethod
    def _normalize_field_name(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.lower())

    @staticmethod
    def _normalize_class_name(class_name: str | None) -> str:
        value = (class_name or "").strip().lower()
        return (
            value.replace("ô", "o")
            .replace("é", "e")
            .replace("è", "e")
            .replace("ê", "e")
            .replace("à", "a")
            .replace("ï", "i")
        )

    @staticmethod
    def _as_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on", "oui"}
        return bool(value)

    @classmethod
    def _derive_speed(cls, character) -> str:
        explicit_speed_keys = ("speed", "walk_speed", "movement_speed")
        for key in explicit_speed_keys:
            raw_value = getattr(character, key, None)
            if raw_value in (None, ""):
                continue
            if isinstance(raw_value, dict):
                walk = raw_value.get("walk")
                if walk not in (None, ""):
                    return str(walk)
                continue
            return str(raw_value)

        normalized_race = cls._normalize_class_name(getattr(character, "race", ""))
        for species_name, species_rules in SPECIES_RULES.items():
            if cls._normalize_class_name(species_name) == normalized_race:
                return str(species_rules.get("speed", 30))
        return "30"

    @staticmethod
    def _extract_roleplay_traits(character) -> dict[str, str]:
        fields = {
            "personality_traits": "personality_traits",
            "ideals": "ideals",
            "bonds": "bonds",
            "flaws": "flaws",
        }
        return {
            key: str(getattr(character, attr, "") or "")
            for key, attr in fields.items()
        }

    @staticmethod
    def _to_multiline(value: str | None) -> str:
        """Transforme les listes compactes en lignes lisibles pour les zones PDF."""
        if not value:
            return ""
        parts = [part.strip() for part in re.split(r"\s*(?:,|;|\|)\s*", value) if part.strip()]
        return "\n".join(parts) if parts else (value or "")

    @staticmethod
    def _normalize_multiline(value: str | None, *, width: int, max_lines: int) -> str:
        """Normalise les blocs texte longs avec retours a la ligne maitrises."""
        if not value:
            return ""
        normalized = " ".join(str(value).split())
        if not normalized:
            return ""
        wrapped_lines = re.findall(rf".{{1,{width}}}(?:\s+|$)", normalized)
        lines = [line.strip() for line in wrapped_lines if line.strip()]
        return "\n".join(lines[:max_lines])

    @staticmethod
    def _split_spell_list(value: str | None) -> list[str]:
        if not value:
            return []
        return [part.strip() for part in re.split(r"\s*(?:,|;|\|)\s*", value) if part.strip()]

    @staticmethod
    def _normalize_text_key(value: str | None) -> str:
        if not value:
            return ""
        normalized = unicodedata.normalize("NFKD", str(value))
        ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", ascii_only.lower())).strip()

    @classmethod
    def _resolve_weapon_profile(cls, weapon_name: str) -> dict[str, Any] | None:
        normalized_name = cls._normalize_text_key(weapon_name)
        if not normalized_name:
            return None

        for weapon in cls._load_weapons_catalog():
            weapon_id = cls._normalize_text_key(weapon.get("id"))
            fr_name = cls._normalize_text_key(weapon.get("name_fr"))
            en_name = cls._normalize_text_key(weapon.get("name_en"))
            if normalized_name not in {weapon_id, fr_name, en_name}:
                continue

            damage = weapon.get("damage") if isinstance(weapon.get("damage"), dict) else {}
            attack_type = str(weapon.get("attack_type") or "").lower()
            properties = {str(prop).lower() for prop in weapon.get("properties", []) if prop}
            return {
                "name": weapon.get("name_fr") or weapon.get("name_en") or weapon.get("id") or weapon_name,
                "damage": str(damage.get("dice") or ""),
                "damage_type": cls.DAMAGE_TYPE_FR.get(str(damage.get("type") or "").lower(), str(damage.get("type") or "")),
                "is_ranged": attack_type == "ranged",
                "finesse": "finesse" in properties,
            }

        if normalized_name in cls.WEAPON_PROFILES:
            return cls.WEAPON_PROFILES[normalized_name]

        for key, profile in cls.WEAPON_PROFILES.items():
            if normalized_name in key or key in normalized_name:
                return profile
        return None

    @classmethod
    def _load_weapons_catalog(cls) -> list[dict[str, Any]]:
        if cls._WEAPONS_CATALOG_CACHE is not None:
            return cls._WEAPONS_CATALOG_CACHE
        weapons_catalog_path = Path(__file__).resolve().parents[2] / "data" / "weapons_catalog.json"
        try:
            payload = json.loads(weapons_catalog_path.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("Impossible de charger weapons_catalog.json")
            return []
        cls._WEAPONS_CATALOG_CACHE = payload if isinstance(payload, list) else []
        return cls._WEAPONS_CATALOG_CACHE

    @staticmethod
    def _extract_weapon_loadouts(equipment_value: str | None) -> list[str]:
        if not equipment_value:
            return []

        selected: list[str] = []

        chunks = [chunk.strip() for chunk in (equipment_value or "").split("|") if chunk.strip()]
        for chunk in chunks:
            normalized_chunk = CharacterSheetPdfService._normalize_text_key(chunk)
            if normalized_chunk.startswith("arme de corps a corps equipee"):
                name = re.sub(r"^.*?:\s*", "", chunk, count=1).strip()
                if name:
                    selected.append(name)
            elif normalized_chunk.startswith("arme a distance equipee"):
                name = re.sub(r"^.*?:\s*", "", chunk, count=1).strip()
                if name:
                    selected.append(name)
        return list(dict.fromkeys(selected))

    @classmethod
    def _build_attacks_spellcasting_text(cls, character) -> str:
        rows = cls._build_weapon_table_rows(character, max_rows=5)
        if not rows:
            return ""

        def clamp_line(value: str, limit: int = 36) -> str:
            text = " ".join((value or "").split())
            if len(text) <= limit:
                return text
            return f"{text[:limit - 1].rstrip()}…"

        lines: list[str] = []
        for row in rows:
            if row["attack_bonus"] and row["damage_type"]:
                lines.append(clamp_line(f"{row['name']} {row['attack_bonus']} {row['damage_type']}"))
            else:
                lines.append(clamp_line(row["name"]))
        return "\n".join(lines)

    @classmethod
    def _build_weapon_table_rows(cls, character, *, max_rows: int = 3) -> list[dict[str, str]]:
        weapon_names = cls._extract_weapon_loadouts(character.equipment)
        if not weapon_names:
            return []

        damage_type_short = {
            "Tranchant": "Trch",
            "Percant": "Perc",
            "Contondant": "Cont",
        }
        rows: list[dict[str, str]] = []
        for weapon_name in weapon_names[:max_rows]:
            profile = cls._resolve_weapon_profile(weapon_name)
            if not profile:
                rows.append({"name": weapon_name, "attack_bonus": "", "damage_type": ""})
                continue

            if profile["is_ranged"]:
                ability_mod = character.mod_dexterite
            elif profile["finesse"]:
                ability_mod = max(character.mod_force, character.mod_dexterite)
            else:
                ability_mod = character.mod_force

            attack_bonus = cls._format_mod(ability_mod + character.bonus_maitrise)
            damage_bonus = f"+{ability_mod}" if ability_mod >= 0 else str(ability_mod)
            damage_type = damage_type_short.get(profile["damage_type"], profile["damage_type"])
            rows.append(
                {
                    "name": str(profile.get("name") or weapon_name),
                    "attack_bonus": attack_bonus,
                    "damage_type": f"{profile['damage']}{damage_bonus} {damage_type}",
                }
            )
        return rows

    @classmethod
    def _build_dynamic_spell_field_values(
        cls,
        character,
        field_names: list[str],
        existing_values: dict[str, str],
    ) -> dict[str, str]:
        """Mappe dynamiquement les sorts choisis vers les champs de la page sorts du PDF."""
        selected_spells = list(
            dict.fromkeys(
                cls._split_spell_list(character.selected_cantrips)
                + cls._split_spell_list(character.selected_level_1_spells)
            )
        )
        if not selected_spells:
            return {}

        candidate_fields: list[str] = []
        for field_name in field_names:
            normalized = field_name.strip().lower()
            if not normalized:
                continue
            if any(
                blocked in normalized
                for blocked in (
                    "spellcasting",
                    "spellsavedc",
                    "spell save dc",
                    "spell attack bonus",
                    "spellatkbonus",
                    "attacks",
                    "attack",
                    "slots",
                    "slot",
                    "prepared",
                    "checkbox",
                )
            ):
                continue
            looks_like_spell_name_field = (
                "cantrip" in normalized
                or bool(re.search(r"\bspell\b", normalized))
                or bool(re.search(r"\bspells?\s*\d+\b", normalized))
            )
            if looks_like_spell_name_field:
                candidate_fields.append(field_name)

        if not candidate_fields:
            return {}

        def field_sort_key(name: str) -> tuple[int, str]:
            numbers = re.findall(r"\d+", name)
            return (int(numbers[0]), name.lower()) if numbers else (10**9, name.lower())

        candidate_fields = sorted(dict.fromkeys(candidate_fields), key=field_sort_key)
        dynamic_values: dict[str, str] = {}
        for field_name, spell_name in zip(candidate_fields, selected_spells):
            if existing_values.get(field_name):
                continue
            dynamic_values[field_name] = spell_name
        return dynamic_values

    @staticmethod
    def _split_background_payload(value: str | None) -> tuple[str, str]:
        """Retourne (background court, backstory libre) depuis la valeur stockee."""
        raw = (value or "").strip()
        if not raw:
            return "", ""
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if not lines:
            return "", ""
        if len(lines) == 1:
            return lines[0], ""
        return lines[0], "\n".join(lines[1:])

    @classmethod
    def _derive_spellcasting_from_class(cls, character) -> tuple[str, str, str, str]:
        spellcasting_by_class = {
            "artificier": ("INT", character.mod_intelligence),
            "bard": ("CHA", character.mod_charisme),
            "barde": ("CHA", character.mod_charisme),
            "clerc": ("WIS", character.mod_sagesse),
            "cleric": ("WIS", character.mod_sagesse),
            "druide": ("WIS", character.mod_sagesse),
            "druid": ("WIS", character.mod_sagesse),
            "ensorceleur": ("CHA", character.mod_charisme),
            "magicien": ("INT", character.mod_intelligence),
            "occultiste": ("CHA", character.mod_charisme),
            "paladin": ("CHA", character.mod_charisme),
            "ranger": ("WIS", character.mod_sagesse),
            "rodeur": ("WIS", character.mod_sagesse),
            "rôdeur": ("WIS", character.mod_sagesse),
            "sorcerer": ("CHA", character.mod_charisme),
            "warlock": ("CHA", character.mod_charisme),
            "wizard": ("INT", character.mod_intelligence),
        }
        normalized_class = cls._normalize_class_name(character.character_class)
        if normalized_class not in spellcasting_by_class:
            return "", "", "", ""

        ability_code, ability_mod = spellcasting_by_class[normalized_class]
        proficiency_bonus = character.bonus_maitrise
        save_dc = 8 + proficiency_bonus + ability_mod
        attack_bonus = proficiency_bonus + ability_mod
        return character.character_class or "", ability_code, str(save_dc), cls._format_mod(attack_bonus)

    @classmethod
    def _find_template_path(cls, upload_folder: str, template_filename: str | None = None) -> Path:
        if template_filename:
            custom_template = Path(upload_folder) / template_filename
            if not custom_template.exists():
                raise ValueError(f"Template PDF introuvable: {template_filename}")
            return custom_template

        env_template = os.environ.get("DND5_CHARACTER_SHEET_TEMPLATE")
        search_paths = []

        if env_template:
            search_paths.append(Path(env_template))

        # Priorite: template officiel place dans le dossier upload actif.
        search_paths.append(Path(upload_folder) / cls.TEMPLATE_FILENAME)
        search_paths.extend(Path(upload_folder) / name for name in cls.LEGACY_TEMPLATE_FILENAMES)

        # Fallback pour les environnements legacy du projet.
        search_paths.append(cls.STATIC_UPLOADS_DIR / cls.TEMPLATE_FILENAME)
        search_paths.extend(cls.STATIC_UPLOADS_DIR / name for name in cls.LEGACY_TEMPLATE_FILENAMES)

        resolved = next((path for path in search_paths if path.exists()), None)
        if not resolved:
            expected = ", ".join(str(path) for path in search_paths)
            raise ValueError(
                "Template PDF officiel introuvable. "
                f"Chemins testes: {expected}"
            )
        return resolved

    @staticmethod
    def list_pdf_fields(template_path: str | Path) -> list[str]:
        """Retourne la liste brute des noms de champs PDF du template."""
        reader = PdfReader(str(template_path))
        return CharacterSheetPdfService._extract_pdf_field_names(reader)

    @classmethod
    def _extract_pdf_field_names(cls, reader: PdfReader) -> list[str]:
        """Extrait les noms de champs en combinant AcroForm et annotations."""
        names: set[str] = set()

        raw_fields = reader.get_fields() or {}
        names.update(raw_fields.keys())

        for page in reader.pages:
            annotations = page.get("/Annots", [])
            for annotation_ref in annotations:
                annotation = annotation_ref.get_object()
                field_name = annotation.get("/T")
                if field_name:
                    names.add(str(field_name))

                parent = annotation.get("/Parent")
                if parent:
                    parent_obj = parent.get_object()
                    parent_name = parent_obj.get("/T")
                    if parent_name:
                        names.add(str(parent_name))

        return sorted(names)

    @classmethod
    def _resolve_field_mapping(cls, template_path: Path) -> dict[str, str]:
        """Construit le mapping metier -> vrais noms de champs PDF."""
        field_names = cls.list_pdf_fields(template_path)
        normalized_to_real = {
            cls._normalize_field_name(field_name): field_name for field_name in field_names
        }

        mapping: dict[str, str] = {}
        for business_key, aliases in cls.FIELD_ALIASES.items():
            for alias in aliases:
                normalized_alias = cls._normalize_field_name(alias)
                if normalized_alias in normalized_to_real:
                    mapping[business_key] = normalized_to_real[normalized_alias]
                    break

        critical_missing = [key for key in ("character_name", "class_level") if key not in mapping]
        if critical_missing:
            preview = ", ".join(field_names[:20]) if field_names else "aucun"
            raise ValueError(
                "Echec extraction/mapping des champs PDF critiques. "
                f"Manquants: {', '.join(critical_missing)}. "
                f"Exemple de champs detectes: {preview}"
            )

        return mapping

    @classmethod
    def _build_field_values(cls, character, resolved_mapping: dict[str, str]) -> dict[str, str]:
        raw_skills = (character.skill_proficiencies or "").lower()
        normalized_skills = {token.strip() for token in re.split(r"[,;/|]", raw_skills) if token.strip()}

        def has_skill(*terms: str) -> bool:
            return any(term.lower() in normalized_skills for term in terms)

        skill_flags = {
            "acrobatics": has_skill("acrobatics", "acrobaties"),
            "animal_handling": has_skill("animal handling", "dressage"),
            "arcana": has_skill("arcana", "arcanes"),
            "athletics": has_skill("athletics", "athletisme"),
            "deception": has_skill("deception", "tromperie"),
            "history": has_skill("history", "histoire"),
            "insight": has_skill("insight", "intuition"),
            "intimidation": has_skill("intimidation"),
            "investigation": has_skill("investigation"),
            "medicine": has_skill("medicine", "medecine"),
            "nature": has_skill("nature"),
            "perception": has_skill("perception"),
            "performance": has_skill("performance"),
            "persuasion": has_skill("persuasion"),
            "religion": has_skill("religion"),
            "sleight_of_hand": has_skill("sleight of hand", "escamotage"),
            "stealth": has_skill("stealth", "discretion"),
            "survival": has_skill("survival", "survie"),
        }

        skill_values = {}
        for skill_key, ability_key in cls.SKILL_TO_ABILITY.items():
            ability_mod = getattr(character, f"mod_{ability_key}", 0)
            bonus = character.bonus_maitrise if skill_flags[skill_key] else 0
            skill_values[skill_key] = cls._format_mod(ability_mod + bonus)

        spellcasting_class, spellcasting_ability, spell_save_dc, spell_attack_bonus = cls._derive_spellcasting_from_class(character)
        attacks_spellcasting = cls._build_attacks_spellcasting_text(character)
        weapon_rows = cls._build_weapon_table_rows(character, max_rows=3)
        proficiencies_languages = ", ".join(filter(None, [character.skill_proficiencies or "", character.languages or ""]))
        background_name, backstory_text = cls._split_background_payload(character.background_story)
        roleplay_traits = cls._extract_roleplay_traits(character)
        features_traits_source = character.additional_features_traits or character.notes

        values_by_business_key: dict[str, Any] = {
            "character_name": character.name or "",
            "class_level": f"{character.character_class or ''} {character.level or 1}".strip(),
            "background": background_name,
            "player_name": character.player_name or "",
            "race": character.race or "",
            "alignment": character.alignment or "",
            "experience_points": str(character.current_xp or 0),
            "strength": str(character.force or 10),
            "strength_mod": cls._format_mod(character.mod_force),
            "dexterity": str(character.dexterite or 10),
            "dexterity_mod": cls._format_mod(character.mod_dexterite),
            "constitution": str(character.constitution or 10),
            "constitution_mod": cls._format_mod(character.mod_constitution),
            "intelligence": str(character.intelligence or 10),
            "intelligence_mod": cls._format_mod(character.mod_intelligence),
            "wisdom": str(character.sagesse or 10),
            "wisdom_mod": cls._format_mod(character.mod_sagesse),
            "charisma": str(character.charisme or 10),
            "charisma_mod": cls._format_mod(character.mod_charisme),
            "proficiency_bonus": cls._format_mod(character.bonus_maitrise),
            "armor_class": str(character.ac_total),
            "initiative": cls._format_mod(character.initiative_bonus or 0),
            "speed": cls._derive_speed(character),
            "hp_max": str(character.hp_max or 0),
            "hp_current": str(character.hp_current_effective),
            "temp_hp": str(character.temp_hp or 0),
            "languages": character.languages or "",
            "proficiencies_languages": cls._normalize_multiline(proficiencies_languages, width=22, max_lines=8),
            "equipment": cls._normalize_multiline(character.equipment, width=24, max_lines=10),
            "features_traits": cls._normalize_multiline(features_traits_source, width=30, max_lines=16),
            "passive_wisdom": str(10 + character.mod_sagesse + (character.bonus_maitrise if skill_flags["perception"] else 0)),
            "proficiency_checkbox": "Yes" if cls._as_bool(getattr(character, "inspiration", False)) else "Off",
            "age": str(character.age or ""),
            "height": character.height or "",
            "weight": character.weight or "",
            "eyes": character.eyes or "",
            "skin": character.skin or "",
            "hair": character.hair or "",
            "personality_traits": cls._normalize_multiline(roleplay_traits["personality_traits"], width=30, max_lines=6),
            "ideals": cls._normalize_multiline(roleplay_traits["ideals"], width=30, max_lines=6),
            "bonds": cls._normalize_multiline(roleplay_traits["bonds"], width=30, max_lines=6),
            "flaws": cls._normalize_multiline(roleplay_traits["flaws"], width=30, max_lines=6),
            "attacks_spellcasting": attacks_spellcasting,
            "weapon_1_name": weapon_rows[0]["name"] if len(weapon_rows) > 0 else "",
            "weapon_1_attack_bonus": weapon_rows[0]["attack_bonus"] if len(weapon_rows) > 0 else "",
            "weapon_1_damage_type": weapon_rows[0]["damage_type"] if len(weapon_rows) > 0 else "",
            "weapon_2_name": weapon_rows[1]["name"] if len(weapon_rows) > 1 else "",
            "weapon_2_attack_bonus": weapon_rows[1]["attack_bonus"] if len(weapon_rows) > 1 else "",
            "weapon_2_damage_type": weapon_rows[1]["damage_type"] if len(weapon_rows) > 1 else "",
            "weapon_3_name": weapon_rows[2]["name"] if len(weapon_rows) > 2 else "",
            "weapon_3_attack_bonus": weapon_rows[2]["attack_bonus"] if len(weapon_rows) > 2 else "",
            "weapon_3_damage_type": weapon_rows[2]["damage_type"] if len(weapon_rows) > 2 else "",
            "allies_organizations": cls._normalize_multiline(character.allies_organizations, width=32, max_lines=12),
            "character_appearance": cls._normalize_multiline(character.character_appearance, width=30, max_lines=16),
            "additional_features_traits": cls._normalize_multiline(character.additional_features_traits, width=32, max_lines=16),
            "treasure": cls._normalize_multiline(character.treasure, width=30, max_lines=12),
            "character_backstory": backstory_text,
            "armor_class_badge": str(character.ac_total),
            "symbol_name": character.symbol_name or "",
            "spellcasting_class": spellcasting_class,
            "spellcasting_ability": spellcasting_ability,
            "spell_save_dc": spell_save_dc,
            "spell_attack_bonus": spell_attack_bonus,
            "saving_throw_strength": cls._format_mod(character.sauvegarde_force),
            "saving_throw_dexterity": cls._format_mod(character.sauvegarde_dexterite),
            "saving_throw_constitution": cls._format_mod(character.sauvegarde_constitution),
            "saving_throw_intelligence": cls._format_mod(character.sauvegarde_intelligence),
            "saving_throw_wisdom": cls._format_mod(character.sauvegarde_sagesse),
            "saving_throw_charisma": cls._format_mod(character.sauvegarde_charisme),
            "saving_throw_strength_prof": "Yes" if character.maitrise_force else "Off",
            "saving_throw_dexterity_prof": "Yes" if character.maitrise_dexterite else "Off",
            "saving_throw_constitution_prof": "Yes" if character.maitrise_constitution else "Off",
            "saving_throw_intelligence_prof": "Yes" if character.maitrise_intelligence else "Off",
            "saving_throw_wisdom_prof": "Yes" if character.maitrise_sagesse else "Off",
            "saving_throw_charisma_prof": "Yes" if character.maitrise_charisme else "Off",
        }
        values_by_business_key.update(skill_values)
        values_by_business_key.update({f"{skill_key}_prof": "Yes" if is_proficient else "Off" for skill_key, is_proficient in skill_flags.items()})

        resolved_values = {
            resolved_mapping[business_key]: str(value)
            for business_key, value in values_by_business_key.items()
            if business_key in resolved_mapping and value is not None
        }
        for business_key, pdf_key in resolved_mapping.items():
            logger.info(
                "PDF map | app=%s | pdf=%s | value=%r",
                business_key,
                pdf_key,
                resolved_values.get(pdf_key),
            )
        return resolved_values

    @staticmethod
    def _shrink_text_fields(writer: PdfWriter, font_size: int = 8) -> None:
        """Reduit legerement la taille de police des champs texte pour limiter les debordements."""
        for page in writer.pages:
            annotations = page.get("/Annots", [])
            for annotation_ref in annotations:
                annotation = annotation_ref.get_object()
                if annotation.get("/FT") != "/Tx":
                    continue
                annotation[NameObject("/DA")] = TextStringObject(f"/Helv {font_size} Tf 0 g")

    @classmethod
    def generate(cls, character, upload_folder: str, template_filename: str | None = None) -> str:
        """Genere un PDF de fiche pour un personnage et retourne le nom de fichier produit."""
        template_path = cls._find_template_path(upload_folder, template_filename)

        output_filename = f"character_sheet_{character.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
        output_path = Path(upload_folder) / output_filename

        # On ne modifie jamais le template source : on lit puis on ecrit dans un nouveau fichier.
        template_reader = PdfReader(str(template_path))
        resolved_mapping = cls._resolve_field_mapping(template_path)
        field_values = cls._build_field_values(character, resolved_mapping)
        field_values.update(
            cls._build_dynamic_spell_field_values(
                character,
                cls._extract_pdf_field_names(template_reader),
                field_values,
            )
        )
        writer = PdfWriter()
        writer.clone_document_from_reader(template_reader)
        writer.set_need_appearances_writer(True)
        if "/AcroForm" in writer._root_object:
            writer._root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)

        for page in writer.pages:
            writer.update_page_form_field_values(page, field_values, auto_regenerate=False)
        cls._shrink_text_fields(writer, font_size=8)

        with open(output_path, "wb") as output_stream:
            writer.write(output_stream)

        return output_filename
