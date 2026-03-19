# Migrated to application layer
"""Service métier pour la gestion des templates"""
import json
import os
import uuid
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import CharacterTemplate, EncounterTemplate, Combatant
from app.models.user import User
from app.utils import MONSTER_TEMPLATES, allowed_file
from app.utils.dnd5_rules import resolve_character_creation
from app.utils.spell_catalog import get_cantrips, get_spells_for_level
from app.application.use_cases.notification_service import NotificationService
from app.application.use_cases.character_sheet_pdf_service import CharacterSheetPdfService


class TemplateService:
    """Service pour la gestion des templates de personnages et rencontres"""
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

    @staticmethod
    def _normalize_skill_proficiencies(form_data):
        """Normalise les competences maitrisees depuis les checkboxes (ou texte legacy)."""
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
    def _validate_skill_proficiencies_limit(cls, character_class, normalized_skill_proficiencies):
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
    def _validate_selected_spells_exist(normalized_spells, valid_spells, label):
        if not normalized_spells:
            return
        valid_names = {spell["name"] for spell in valid_spells}
        selected_names = [item.strip() for item in normalized_spells.split(",") if item.strip()]
        invalid_names = [name for name in selected_names if name not in valid_names]
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
        for spell_name in selected_cantrip_names + selected_level_one_names:
            spell = catalog_index.get(spell_name)
            if not spell:
                continue
            raw_classes = [str(item).strip().lower() for item in (spell.get("classes") or []) if str(item).strip()]
            if raw_classes and class_key_canonical not in raw_classes:
                raise ValueError(
                    f"Le sort '{spell_name}' n'est pas disponible pour la classe '{character_class}'."
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
        base_equipment = (form_data.get('equipment') or '').strip()
        skill_proficiencies = TemplateService._normalize_skill_proficiencies(form_data) or ''
        tool_proficiencies = (form_data.get('tool_proficiencies') or '').strip()
        weapon_loadout = (form_data.get('weapon_loadout') or '').strip()
        armor_loadout = (form_data.get('armor_loadout') or '').strip()
        inventory_items = (form_data.get('inventory_items') or '').strip()
        spellbook_notes = (form_data.get('spellbook_notes') or '').strip()

        sections = []
        if base_equipment:
            sections.append(f"Equipement principal: {base_equipment}")
        if weapon_loadout:
            sections.append(f"Armes equipees: {weapon_loadout}")
        if armor_loadout:
            sections.append(f"Armure/Bouclier: {armor_loadout}")
        if inventory_items:
            sections.append(f"Inventaire: {inventory_items}")
        if skill_proficiencies:
            sections.append(f"Competences maitrisees: {skill_proficiencies}")
        if tool_proficiencies:
            sections.append(f"Outils maitrises: {tool_proficiencies}")
        if spellbook_notes:
            sections.append(f"Sorts/Aptitudes: {spellbook_notes}")

        if not sections:
            return None
        return " | ".join(sections)

    @staticmethod
    def split_builder_equipment(equipment_value):
        """Reconstitue les champs du funnel a partir de la chaine equipement stockee."""
        parsed = {
            "equipment": "",
            "weapon_loadout": "",
            "armor_loadout": "",
            "inventory_items": "",
            "skill_proficiencies": "",
            "tool_proficiencies": "",
            "spellbook_notes": "",
        }
        if not equipment_value:
            return parsed

        mapping = {
            "Equipement principal:": "equipment",
            "Armes equipees:": "weapon_loadout",
            "Armure/Bouclier:": "armor_loadout",
            "Inventaire:": "inventory_items",
            "Competences maitrisees:": "skill_proficiencies",
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

        resolved_character = resolve_character_creation(form_data)
        normalized_skill_proficiencies = TemplateService._normalize_skill_proficiencies(form_data)
        TemplateService._validate_skill_proficiencies_limit(
            resolved_character.get('character_class') or form_data.get('character_class'),
            normalized_skill_proficiencies,
        )
        spellcasting_ability, spell_save_dc, spell_attack_bonus = TemplateService._derive_spellcasting_stats(
            resolved_character.get('character_class') or form_data.get('character_class'),
            resolved_character.get('level') or form_data.get('level'),
            resolved_character,
        )
        selected_cantrips = TemplateService._normalize_selected_spells(form_data, 'selected_cantrips')
        selected_level_1_spells = TemplateService._normalize_selected_spells(form_data, 'selected_level_1_spells')
        cantrip_catalog = get_cantrips()
        level_one_catalog = get_spells_for_level(1)
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
            form_data.get('language_1'),
            form_data.get('language_2'),
            form_data.get('language_3'),
        ]
        selected_languages = [language for language in selected_languages if language]
        if len(set(selected_languages)) < 3 or 'Commun' not in selected_languages:
            raise ValueError("Les langues doivent inclure Commun et 2 langues distinctes.")

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

        if resolved_campaign_id:
            from app.models.campaign import Campaign
            campaign = Campaign.query.get(int(resolved_campaign_id))
            if campaign and campaign not in template.campaigns:
                template.campaigns.append(campaign)

        should_generate_pdf = bool(form_data.get('generate_pdf_sheet'))
        if should_generate_pdf:
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
    def update_character_template(template_id, form_data, files, upload_folder):
        """Mettre à jour un template de personnage"""
        template = CharacterTemplate.query.get_or_404(template_id)

        # Mise à jour des données de base
        template.name = form_data['name']
        template.character_class = form_data['character_class']
        template.race = form_data.get('race') or template.race
        template.background_story = TemplateService._compose_background_payload(form_data)
        template.level = int(form_data['level'])
        template.hp_max = int(form_data['hp_max'])
        template.hp_current = template.hp_max if template.hp_current is None else min(template.hp_current, template.hp_max)
        template.ac_base = int(form_data['ac_base'])
        template.initiative_bonus = int(form_data['initiative_bonus'])
        template.notes = form_data.get('notes', '')
        template.player_private_notes = form_data.get('player_private_notes', '')
        template.player_name = form_data.get('player_name') or None
        template.campaign_name = form_data.get('campaign_name') or None
        template.gender = form_data.get('gender') or form_data.get('genre') or None
        template.alignment = form_data.get('alignment') or None
        template.languages = form_data.get('languages') or template.languages
        template.height = form_data.get('height') or None
        template.weight = form_data.get('weight') or None
        template.eyes = form_data.get('eyes') or None
        template.skin = form_data.get('skin') or None
        template.hair = form_data.get('hair') or None
        detailed_equipment = TemplateService._compose_builder_equipment(form_data)
        template.equipment = detailed_equipment or form_data.get('equipment') or None
        template.skill_proficiencies = TemplateService._normalize_skill_proficiencies(form_data)
        TemplateService._validate_skill_proficiencies_limit(
            form_data.get('character_class') or template.character_class,
            template.skill_proficiencies,
        )
        template.age = int(form_data.get('age')) if form_data.get('age') else template.age
        template.character_appearance = form_data.get('character_appearance') or None
        template.allies_organizations = form_data.get('allies_organizations') or None
        template.additional_features_traits = form_data.get('additional_features_traits') or None
        template.treasure = form_data.get('treasure') or None
        template.symbol_name = form_data.get('symbol_name') or None
        spellcasting_ability, spell_save_dc, spell_attack_bonus = TemplateService._derive_spellcasting_stats(
            form_data.get('character_class') or template.character_class,
            form_data.get('level') or template.level,
            {
                'force': int(form_data.get('force', template.force or 10) or 10),
                'dexterite': int(form_data.get('dexterite', template.dexterite or 10) or 10),
                'constitution': int(form_data.get('constitution', template.constitution or 10) or 10),
                'intelligence': int(form_data.get('intelligence', template.intelligence or 10) or 10),
                'sagesse': int(form_data.get('sagesse', template.sagesse or 10) or 10),
                'charisme': int(form_data.get('charisme', template.charisme or 10) or 10),
            },
        )
        template.spellcasting_class = form_data.get('character_class') or template.character_class
        template.spellcasting_ability = spellcasting_ability
        template.spell_save_dc = spell_save_dc
        template.spell_attack_bonus = spell_attack_bonus
        if 'selected_cantrips' in form_data:
            template.selected_cantrips = TemplateService._normalize_selected_spells(form_data, 'selected_cantrips')
        if 'selected_level_1_spells' in form_data:
            template.selected_level_1_spells = TemplateService._normalize_selected_spells(form_data, 'selected_level_1_spells')
        cantrip_catalog = get_cantrips()
        level_one_catalog = get_spells_for_level(1)
        TemplateService._validate_selected_spells_exist(template.selected_cantrips, cantrip_catalog, "Sorts mineurs")
        TemplateService._validate_selected_spells_exist(template.selected_level_1_spells, level_one_catalog, "Sorts de niveau 1")
        TemplateService._validate_spell_selection_rules(
            form_data.get('character_class') or template.character_class,
            template.selected_cantrips,
            template.selected_level_1_spells,
            cantrip_catalog,
            level_one_catalog,
        )

        # ✅ AJOUT : Gestion du champ is_public
        template.is_public = bool(form_data.get('is_public', False))
        template.visibility_level = form_data.get('visibility_level', 'private')

        # Mise à jour des caractéristiques
        template.force = int(form_data.get('force', 10))
        template.dexterite = int(form_data.get('dexterite', 10))
        template.constitution = int(form_data.get('constitution', 10))
        template.intelligence = int(form_data.get('intelligence', 10))
        template.sagesse = int(form_data.get('sagesse', 10))
        template.charisme = int(form_data.get('charisme', 10))

        # Mise à jour des maîtrises
        template.maitrise_force = 'maitrise_force' in form_data
        template.maitrise_dexterite = 'maitrise_dexterite' in form_data
        template.maitrise_constitution = 'maitrise_constitution' in form_data
        template.maitrise_intelligence = 'maitrise_intelligence' in form_data
        template.maitrise_sagesse = 'maitrise_sagesse' in form_data
        template.maitrise_charisme = 'maitrise_charisme' in form_data

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
            ac_bonus=template.ac_bonus or 0,
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
