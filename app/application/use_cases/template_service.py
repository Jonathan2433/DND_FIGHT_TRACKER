# Migrated to application layer
"""Service métier pour la gestion des templates"""
import json
import os
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import CharacterTemplate, EncounterTemplate, Combatant
from app.utils import MONSTER_TEMPLATES, allowed_file
from app.utils.dnd5_rules import resolve_character_creation
from app.application.use_cases.notification_service import NotificationService


class TemplateService:
    """Service pour la gestion des templates de personnages et rencontres"""

    @staticmethod
    def create_character_template(form_data, files, upload_folder, current_user_id=None, campaign_id=None):
        """Créer un nouveau template de personnage"""
        image = files.get("image")
        pdf = files.get("pdf")
        filename = None
        pdf_filename = None

        # Gestion de l'image
        if image and image.filename != "" and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(upload_folder, filename))

        # Gestion du PDF
        if pdf and pdf.filename != "" and pdf.filename.lower().endswith(".pdf"):
            pdf_filename = secure_filename(pdf.filename)
            pdf.save(os.path.join(upload_folder, pdf_filename))

        # ✅ CORRECTION : Récupérer l'utilisateur connecté
        from flask import session
        current_user_id = current_user_id or session.get('user_id')
        if not current_user_id:
            raise ValueError("Aucun utilisateur connecté")

        resolved_campaign_id = campaign_id if campaign_id is not None else form_data.get('campaign_id')

        resolved_character = resolve_character_creation(form_data)

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
            ac_base=resolved_character['ac_base'],
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
            notes=form_data.get('notes', ''),
            player_private_notes=form_data.get('player_private_notes', ''),
            current_xp=int(form_data.get('current_xp', 0))
        )

        db.session.add(template)
        db.session.flush()

        if resolved_campaign_id:
            from app.models.campaign import Campaign
            campaign = Campaign.query.get(int(resolved_campaign_id))
            if campaign and campaign not in template.campaigns:
                template.campaigns.append(campaign)

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
        template.level = int(form_data['level'])
        template.hp_max = int(form_data['hp_max'])
        template.ac_base = int(form_data['ac_base'])
        template.initiative_bonus = int(form_data['initiative_bonus'])
        template.notes = form_data.get('notes', '')
        template.player_private_notes = form_data.get('player_private_notes', '')

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
            filename = secure_filename(image.filename)
            image.save(os.path.join(upload_folder, filename))
            template.image_filename = filename

        pdf = files.get("pdf")
        if pdf and pdf.filename != "" and pdf.filename.lower().endswith(".pdf"):
            pdf_filename = secure_filename(pdf.filename)
            pdf.save(os.path.join(upload_folder, pdf_filename))
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
            name=template.name,
            type="PJ",
            hp_max=template.hp_max,
            hp_current=template.hp_max,
            ac_base=template.ac_base,
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
        for i in range(quantity):
            # Initiative manuelle ou celle du template
            if manual_initiative and manual_initiative.strip() != "":
                initiative_value = int(manual_initiative)
            else:
                initiative_value = template["initiative"]

            combatant = Combatant(
                name=f"{template_name} {i + 1}" if quantity > 1 else template_name,
                type=template["type"],
                hp_max=template["hp"],
                hp_current=template["hp"],
                initiative=initiative_value,
                ac_base=template["ac"],
                ac_bonus=0,
                conditions="",
                combat_id=combat_id,
                notes=monster_image_filename
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
