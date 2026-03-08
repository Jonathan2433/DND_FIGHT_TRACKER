"""Routes pour la gestion des templates et personnages"""
from flask import Blueprint, render_template, request, redirect, url_for, current_app, jsonify
from app.services import TemplateService
from app.models import CharacterTemplate, EncounterTemplate

# Créer le blueprint
bp = Blueprint('template', __name__, url_prefix='/template')


@bp.route('/manage')
def manage_templates():
    """Gestion des templates"""
    characters = CharacterTemplate.query.all()
    encounters = EncounterTemplate.query.all()

    return render_template(
        'templates_manager.html',
        characters=characters,
        encounters=encounters
    )


@bp.route('/character/create', methods=['POST'])
def create_character_template():
    """Créer un template de personnage"""
    template = TemplateService.create_character_template(
        request.form,
        request.files,
        current_app.config['UPLOAD_FOLDER']
    )
    return redirect(url_for('template.manage_templates'))


@bp.route('/character/<int:id>/edit', methods=['GET', 'POST'])
def edit_character_template(id):
    """Modifier un template de personnage"""
    template = CharacterTemplate.query.get_or_404(id)

    if request.method == 'POST':
        TemplateService.update_character_template(
            id,
            request.form,
            request.files,
            current_app.config['UPLOAD_FOLDER']
        )
        return redirect(url_for('template.manage_templates'))

    return render_template("edit_character.html", character=template)


@bp.route('/character/<int:id>/delete', methods=['POST'])
def delete_character_template(id):
    """Supprimer un template de personnage"""
    TemplateService.delete_character_template(id)
    return redirect(url_for('template.manage_templates'))


@bp.route('/character/<int:id>')
def character_profile(id):
    """Profil d'un personnage"""
    character = CharacterTemplate.query.get_or_404(id)
    combats_played = TemplateService.get_character_combat_count(character.name)

    return render_template(
        'character_profile.html',
        character=character,
        combats_played=combats_played
    )


@bp.route('/encounter/create', methods=['POST'])
def create_encounter_template():
    """Créer un template de rencontre"""
    TemplateService.create_encounter_template(request.form)
    return redirect(url_for('template.manage_templates'))


@bp.route('/encounter/<int:id>/edit', methods=['GET', 'POST'])
def edit_encounter_template(id):
    """Modifier un template de rencontre"""
    template = EncounterTemplate.query.get_or_404(id)

    if request.method == 'POST':
        template.name = request.form['name']
        template.description = request.form['description']
        template.difficulty = request.form['difficulty']

        from app.extensions import db
        db.session.commit()

        return redirect(url_for('template.manage_templates'))

    return render_template("edit_encounter.html", encounter=template)


@bp.route('/encounter/<int:id>/delete', methods=['POST'])
def delete_encounter_template(id):
    """Supprimer un template de rencontre"""
    TemplateService.delete_encounter_template(id)
    return redirect(url_for('template.manage_templates'))


@bp.route('/export')
def export_templates():
    """Exporter tous les templates en JSON"""
    export_data = TemplateService.export_templates()
    return jsonify(export_data)