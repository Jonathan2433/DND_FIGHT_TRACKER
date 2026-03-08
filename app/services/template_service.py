"""Service métier pour la gestion des templates"""
import json
import os
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import CharacterTemplate, EncounterTemplate, Combatant
from app.utils import MONSTER_TEMPLATES, allowed_file


class TemplateService:
    """Service pour la gestion des templates de personnages et rencontres"""

    @staticmethod
    def create_character_template(form_data, files, upload_folder):
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

        template = CharacterTemplate(
            name=form_data['name'],
            character_class=form_data['character_class'],
            level=int(form_data['level']),
            hp_max=int(form_data['hp_max']),
            ac_base=int(form_data['ac_base']),
            initiative_bonus=int(form_data['initiative_bonus']),

            # Caractéristiques
            force=int(form_data.get('force', 10)),
            dexterite=int(form_data.get('dexterite', 10)),
            constitution=int(form_data.get('constitution', 10)),
            intelligence=int(form_data.get('intelligence', 10)),
            sagesse=int(form_data.get('sagesse', 10)),
            charisme=int(form_data.get('charisme', 10)),

            # Maîtrises de sauvegarde
            maitrise_force='maitrise_force' in form_data,
            maitrise_dexterite='maitrise_dexterite' in form_data,
            maitrise_constitution='maitrise_constitution' in form_data,
            maitrise_intelligence='maitrise_intelligence' in form_data,
            maitrise_sagesse='maitrise_sagesse' in form_data,
            maitrise_charisme='maitrise_charisme' in form_data,

            image_filename=filename,
            pdf_filename=pdf_filename,
            notes=form_data.get('notes', '')
        )

        db.session.add(template)
        db.session.commit()

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

        return template

    @staticmethod
    def create_encounter_template(form_data):
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
    def add_monster_template_to_combat(combat_id, template_name, quantity, manual_initiative=None):
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
                combat_id=combat_id
            )

            db.session.add(combatant)
            created_combatants.append(combatant)

        db.session.commit()

        return created_combatants

    @staticmethod
    def delete_character_template(template_id):
        """Supprimer un template de personnage"""
        template = CharacterTemplate.query.get_or_404(template_id)
        db.session.delete(template)
        db.session.commit()

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
    def export_templates():
        """Exporter tous les templates en JSON"""
        characters = CharacterTemplate.query.all()
        encounters = EncounterTemplate.query.all()

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