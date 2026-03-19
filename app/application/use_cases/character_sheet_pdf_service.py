"""Generation de fiche PDF DnD5 a partir des donnees personnage."""
from __future__ import annotations

import re
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject


class CharacterSheetPdfService:
    """Construit un PDF de fiche personnage depuis le template officiel fillable."""

    TEMPLATE_FILENAME = "5E_CharacterSheet_Fillable.pdf"
    LEGACY_TEMPLATE_FILENAMES = (
        "Feuille_de_personnage_Dungeons__Dragons_-_DD_5_2.pdf",
        "Feuille_de_personnage_Dungeons__Dragons_-_DD_5_1.pdf",
    )
    STATIC_UPLOADS_DIR = Path(__file__).resolve().parents[3] / "static" / "uploads"

    # Mapping metier -> alias possibles dans le PDF officiel.
    # Les alias sont resolves automatiquement vers les vrais noms de champs.
    FIELD_ALIASES: dict[str, tuple[str, ...]] = {
        "character_name": ("CharacterName", "Character Name", "CharName"),
        "class_level": ("ClassLevel", "Class & Level", "ClassLevel1"),
        "background": ("Background",),
        "player_name": ("PlayerName", "Player Name"),
        "race": ("Race",),
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
        "initiative": ("Initiative",),
        "speed": ("Speed",),
        "hp_max": ("HPMax", "HP Max", "Hit Point Maximum"),
        "hp_current": ("HPCurrent", "Current HP", "Current Hit Points"),
        "temp_hp": ("HPTemp", "Temp HP", "Temporary Hit Points"),
        "languages": ("Languages",),
        "proficiencies_languages": ("ProficienciesLang", "Proficiencies & Languages", "Proficiencies and Languages"),
        "equipment": ("Equipment", "EquipmentNotes", "Treasure"),
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
    FIELD_KEYWORDS: dict[str, tuple[str, ...]] = {
        "character_name": ("character", "name"),
        "class_level": ("class", "level"),
        "background": ("background",),
        "player_name": ("player", "name"),
        "race": ("race",),
        "alignment": ("alignment",),
        "experience_points": ("xp", "experience"),
        "strength": ("str", "strength"),
        "strength_mod": ("strmod", "strengthmod"),
        "dexterity": ("dex", "dexterity"),
        "dexterity_mod": ("dexmod", "dexteritymod"),
        "constitution": ("con", "constitution"),
        "constitution_mod": ("conmod", "constitutionmod"),
        "intelligence": ("int", "intelligence"),
        "intelligence_mod": ("intmod", "intelligencemod"),
        "wisdom": ("wis", "wisdom"),
        "wisdom_mod": ("wismod", "wisdommod"),
        "charisma": ("cha", "charisma"),
        "charisma_mod": ("chamod", "charismamod"),
        "proficiency_bonus": ("prof", "proficiency"),
        "armor_class": ("armorclass",),
        "initiative": ("initiative",),
        "speed": ("speed",),
        "hp_max": ("hpmax", "hitpointmaximum"),
        "hp_current": ("hpcurrent", "currenthp"),
        "temp_hp": ("hptemp", "temphp", "temporaryhitpoints"),
        "languages": ("language",),
        "equipment": ("equipment",),
        "features_traits": ("features", "traits"),
        "age": ("age",),
        "height": ("height",),
        "weight": ("weight",),
        "eyes": ("eyes",),
        "skin": ("skin",),
        "hair": ("hair",),
        "allies_organizations": ("allies", "organizations"),
        "character_appearance": ("appearance",),
        "additional_features_traits": ("additional", "features", "traits"),
        "spellcasting_class": ("spellcastingclass",),
        "spellcasting_ability": ("spellcastingability",),
        "spell_save_dc": ("spellsavedc",),
        "spell_attack_bonus": ("spellatkbonus", "spellattackbonus"),
    }

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
            cls._normalize_field_name(field_name): field_name
            for field_name in field_names
        }

        mapping: dict[str, str] = {}
        for business_key, aliases in cls.FIELD_ALIASES.items():
            found_field: str | None = None

            # 1) correspondance exacte normalisee
            for alias in aliases:
                normalized_alias = cls._normalize_field_name(alias)
                if normalized_alias in normalized_to_real:
                    found_field = normalized_to_real[normalized_alias]
                    break

            # 2) fallback en recherche partielle
            if not found_field:
                for alias in aliases:
                    normalized_alias = cls._normalize_field_name(alias)
                    if len(normalized_alias) <= 3:
                        continue
                    partial = [
                        real_name
                        for normalized_name, real_name in normalized_to_real.items()
                        if normalized_alias in normalized_name or normalized_name in normalized_alias
                    ]
                    if partial:
                        found_field = partial[0]
                        break

            if found_field:
                mapping[business_key] = found_field

        if len(mapping) < len(cls.REQUIRED_MAPPING_KEYS):
            for business_key, keywords in cls.FIELD_KEYWORDS.items():
                if business_key in mapping:
                    continue
                for normalized_name, real_name in normalized_to_real.items():
                    if business_key == "armor_class":
                        is_armor_field = (
                            normalized_name in {"ac", "armorclass", "armourclass"}
                            or "armorclass" in normalized_name
                            or "armourclass" in normalized_name
                        )
                        if not is_armor_field:
                            continue
                    if any(keyword in normalized_name for keyword in keywords):
                        mapping[business_key] = real_name
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
        proficiencies_languages = ", ".join(filter(None, [character.skill_proficiencies or "", character.languages or ""]))

        values_by_business_key: dict[str, Any] = {
            "character_name": character.name or "",
            "class_level": f"{character.character_class or ''} {character.level or 1}".strip(),
            "background": character.background_story or "",
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
            "speed": "30",
            "hp_max": str(character.hp_max or 0),
            "hp_current": str(character.hp_current_effective),
            "temp_hp": str(character.temp_hp or 0),
            "languages": character.languages or "",
            "proficiencies_languages": proficiencies_languages[:900],
            "equipment": (character.equipment or "")[:400],
            "features_traits": (character.notes or "")[:900],
            "passive_wisdom": str(10 + character.mod_sagesse + (character.bonus_maitrise if skill_flags["perception"] else 0)),
            "age": str(character.age or ""),
            "height": character.height or "",
            "weight": character.weight or "",
            "eyes": character.eyes or "",
            "skin": character.skin or "",
            "hair": character.hair or "",
            "personality_traits": "\n".join(filter(None, [f"Genre: {character.gender}" if character.gender else "", f"Alignement: {character.alignment}" if character.alignment else ""])),
            "allies_organizations": (character.allies_organizations or "")[:900],
            "character_appearance": (character.character_appearance or "")[:900],
            "additional_features_traits": (character.additional_features_traits or "")[:1200],
            "treasure": (character.treasure or character.equipment or "")[:1200],
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

        return {
            resolved_mapping[business_key]: str(value)
            for business_key, value in values_by_business_key.items()
            if business_key in resolved_mapping and value is not None
        }

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

        resolved_mapping = cls._resolve_field_mapping(template_path)
        field_values = cls._build_field_values(character, resolved_mapping)

        # On ne modifie jamais le template source : on lit puis on ecrit dans un nouveau fichier.
        template_reader = PdfReader(str(template_path))
        writer = PdfWriter()
        writer.clone_document_from_reader(template_reader)
        writer.set_need_appearances_writer(True)

        for page in writer.pages:
            writer.update_page_form_field_values(page, field_values, auto_regenerate=False)
        cls._shrink_text_fields(writer, font_size=8)

        with open(output_path, "wb") as output_stream:
            writer.write(output_stream)

        return output_filename
