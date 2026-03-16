"""Routes pour la gestion des templates et personnages"""
from flask import Blueprint, render_template, request, redirect, url_for, current_app, jsonify, flash
from app.services import TemplateService
from app.models import CharacterTemplate, EncounterTemplate, MonsterProfile
from app.utils import MONSTER_TEMPLATES
from app.utils.decorators import login_required, mj_or_admin_required

# Créer le blueprint
bp = Blueprint('template', __name__, url_prefix='/template')


@bp.route('/manage')
def manage_templates():
    """Gestion des templates"""
    characters = CharacterTemplate.query.all()
    encounters = EncounterTemplate.query.all()
    monster_profiles = {m.monster_name: m.image_filename for m in MonsterProfile.query.all()}

    return render_template(
        'templates_manager.html',
        characters=characters,
        encounters=encounters,
        monster_templates=MONSTER_TEMPLATES,
        monster_profiles=monster_profiles
    )


@bp.route('/monster-profile', methods=['POST'])
@login_required
@mj_or_admin_required
def upsert_monster_profile():
    """Associer une image de profil à un template de monstre."""
    result = TemplateService.save_monster_profile(
        monster_name=request.form.get('monster_name', ''),
        image=request.files.get('image'),
        upload_folder=current_app.config['UPLOAD_FOLDER']
    )

    if 'error' in result:
        flash(result['error'], 'error')
    else:
        flash(result['message'], 'success')

    return redirect(url_for('template.manage_templates'))


@bp.route('/character/create', methods=['POST'])
def create_character_template():
    """Créer un template de personnage"""
    TemplateService.create_character_template(request.form, request.files, current_app.config['UPLOAD_FOLDER'])
    return redirect(url_for('template.manage_templates'))


@bp.route('/character/<int:id>/edit', methods=['GET', 'POST'])
def edit_character_template(id):
    """Modifier un template de personnage"""
    template = CharacterTemplate.query.get_or_404(id)

    if request.method == 'POST':
        TemplateService.update_character_template(id, request.form, request.files, current_app.config['UPLOAD_FOLDER'])
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

    return render_template('character_profile.html', character=character, combats_played=combats_played)


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
