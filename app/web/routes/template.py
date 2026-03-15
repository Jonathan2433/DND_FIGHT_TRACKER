# Migrated to app.web.routes
"""Routes pour la gestion des templates et personnages"""
from flask import Blueprint, render_template, request, redirect, url_for, current_app, jsonify, flash, g
from app.application.use_cases import TemplateService
from app.application.use_cases.campaign_service import CampaignService
from app.models import CharacterTemplate, EncounterTemplate
from app.domain.policies import EncounterTemplatePolicy
from app.utils.decorators import login_required
from app.models.campaign import Campaign
from app.extensions import db
from app.utils.dnd5_rules import RACE_BONUSES, CLASS_RULES, STANDARD_ARRAY

# Créer le blueprint
bp = Blueprint('template', __name__, url_prefix='/template')


@bp.route('/manage')
@login_required
def manage_templates():
    """Gestion des templates"""
    # ✅ MODIFICATION : Ne montrer que les personnages de l'utilisateur connecté
    characters = (
        CharacterTemplate.query.filter_by(owner_id=g.current_user.id, is_active=True)
        .order_by(CharacterTemplate.character_type.asc(), CharacterTemplate.name.asc())
        .all()
    )
    encounters = EncounterTemplate.query.filter_by(owner_id=g.current_user.id).all()
    pj_characters = [character for character in characters if character.character_type == 'PJ']
    other_characters = [character for character in characters if character.character_type != 'PJ']

    campaign_context = None
    campaign_id = request.args.get('campaign_id', type=int)
    if campaign_id:
        campaign_context = CampaignService.get_campaign_with_access_check(campaign_id, g.current_user.id)
        if not campaign_context:
            flash('Campagne invalide ou accès interdit.', 'error')
            return redirect(url_for('template.manage_templates'))

    return render_template(
        'templates_manager.html',
        characters=characters,
        pj_characters=pj_characters,
        other_characters=other_characters,
        encounters=encounters,
        campaign_context=campaign_context,
        dnd_races=sorted(RACE_BONUSES.keys()),
        dnd_classes=sorted(CLASS_RULES.keys()),
        standard_array=STANDARD_ARRAY
    )


@bp.route('/character/create', methods=['POST'])
@login_required  # ✅ AJOUT : Protection obligatoire
def create_character_template():
    """Créer un template de personnage"""
    campaign_id = request.form.get('campaign_id', type=int)

    if campaign_id:
        campaign = CampaignService.get_campaign_with_access_check(campaign_id, g.current_user.id)
        if not campaign:
            flash('Campagne invalide ou accès interdit.', 'error')
            return redirect(url_for('template.manage_templates'))

    TemplateService.create_character_template(
        request.form,
        request.files,
        current_app.config['UPLOAD_FOLDER'],
        current_user_id=g.current_user.id,
        campaign_id=campaign_id
    )

    if campaign_id:
        flash('PJ créé et automatiquement associé à la campagne.', 'success')
        return redirect(url_for('campaign.view_campaign', campaign_id=campaign_id))

    return redirect(url_for('template.manage_templates'))


@bp.route('/character/<int:id>/edit', methods=['GET', 'POST'])
@login_required  # ✅ AJOUT : Protection obligatoire
def edit_character_template(id):
    """Modifier un template de personnage"""
    template = CharacterTemplate.query.get_or_404(id)

    # ✅ AJOUT : Vérifier les permissions d'édition
    if not template.can_be_edited_by(g.current_user):
        flash('Vous n\'êtes pas autorisé à modifier ce personnage.', 'error')
        return redirect(url_for('template.character_profile', id=id))

    if request.method == 'POST':
        TemplateService.update_character_template(
            id,
            request.form,
            request.files,
            current_app.config['UPLOAD_FOLDER']
        )
        flash('Personnage modifié avec succès !', 'success')
        return redirect(url_for('template.character_profile', id=id))

    return render_template("edit_character.html", character=template)


@bp.route('/character/<int:id>/delete', methods=['POST'])
@login_required  # ✅ AJOUT : Protection obligatoire
def delete_character_template(id):
    """Supprimer un template de personnage"""
    template = CharacterTemplate.query.get_or_404(id)

    # ✅ AJOUT : Vérifier les permissions
    if not template.can_be_edited_by(g.current_user):
        flash('Vous n\'êtes pas autorisé à supprimer ce personnage.', 'error')
        return redirect(url_for('template.character_profile', id=id))

    TemplateService.delete_character_template(id)
    flash('Personnage supprimé.', 'success')
    return redirect(url_for('template.manage_templates'))


@bp.route('/character/<int:id>')
# ✅ PAS de @login_required ici - déjà géré dans le LOT 4
def character_profile(id):
    """Profil d'un personnage - Accessible aux publics"""
    character = CharacterTemplate.query.get_or_404(id)

    # ✅ Vérifier les permissions avec l'utilisateur connecté ou None
    from flask import session
    from app.application.use_cases.auth_service import AuthService

    current_user = None
    if 'user_id' in session:
        current_user = AuthService.get_user_by_id(session['user_id'])
        g.current_user = current_user

    # Vérifier si l'utilisateur peut voir ce personnage
    if not character.can_be_viewed_by(current_user):
        flash('Vous n\'êtes pas autorisé à voir ce personnage.', 'error')
        return redirect(url_for('main.index'))

    visible_payload = character.get_visible_data(current_user, character.campaign)
    visibility_mode = visible_payload['level'] if visible_payload else 'private'

    is_full_view = bool(current_user and (
        character.owner_id == current_user.id
        or current_user.role == 'Admin'
        or (character.campaign and current_user.is_mj_of(character.campaign))
        or any(current_user.is_mj_of(c) for c in character.campaigns)
    ))

    limited_profile = bool(
        visible_payload
        and visibility_mode in ['reduced', 'semi_complete']
        and not is_full_view
    )

    combats_played = TemplateService.get_character_combat_count(character.name)
    can_award_xp = False
    is_campaign_mj = False

    if current_user:
        can_award_xp = current_user.role == 'Admin'
        can_manage_from_campaigns = any(current_user.is_mj_of(c) for c in character.campaigns)

        if (character.campaign and current_user.is_mj_of(character.campaign)) or can_manage_from_campaigns:
            can_award_xp = True
            is_campaign_mj = True
        elif not character.campaign and character.owner_id == current_user.id:
            can_award_xp = True

    return render_template(
        'character_profile.html',
        character=character,
        visible_character=visible_payload['data'] if visible_payload else None,
        visibility_mode=visibility_mode,
        limited_profile=limited_profile,
        combats_played=combats_played,
        can_edit=character.can_be_edited_by(current_user) if current_user else False,
        can_award_xp=can_award_xp,
        is_campaign_mj=is_campaign_mj
    )


# ✅ ROUTES RENCONTRES AUSSI SÉCURISÉES

@bp.route('/encounter/create', methods=['POST'])
@login_required  # ✅ AJOUT
def create_encounter_template():
    """Créer un template de rencontre"""
    TemplateService.create_encounter_template(request.form, owner_id=g.current_user.id)
    return redirect(url_for('template.manage_templates'))


@bp.route('/encounter/<int:id>/edit', methods=['GET', 'POST'])
@login_required  # ✅ AJOUT
def edit_encounter_template(id):
    """Modifier un template de rencontre"""
    template = EncounterTemplate.query.get_or_404(id)

    if not EncounterTemplatePolicy.can_manage(g.current_user, template):
        flash('Vous n\'êtes pas autorisé à modifier ce template.', 'error')
        return redirect(url_for('template.manage_templates'))

    if request.method == 'POST':
        template.name = request.form['name']
        template.description = request.form['description']
        template.difficulty = request.form['difficulty']

        from app.extensions import db
        db.session.commit()

        return redirect(url_for('template.manage_templates'))

    return render_template("edit_encounter.html", encounter=template)


@bp.route('/encounter/<int:id>/delete', methods=['POST'])
@login_required  # ✅ AJOUT
def delete_encounter_template(id):
    """Supprimer un template de rencontre"""
    template = EncounterTemplate.query.get_or_404(id)
    if not EncounterTemplatePolicy.can_manage(g.current_user, template):
        flash('Vous n\'êtes pas autorisé à supprimer ce template.', 'error')
        return redirect(url_for('template.manage_templates'))

    TemplateService.delete_encounter_template(id)
    return redirect(url_for('template.manage_templates'))


@bp.route('/export')
@login_required  # ✅ AJOUT
def export_templates():
    """Exporter tous les templates en JSON"""
    export_data = TemplateService.export_templates(owner_id=g.current_user.id)
    return jsonify(export_data)


@bp.route('/character/<int:character_id>/join_campaign', methods=['GET', 'POST'])
@login_required
def join_campaign(character_id):
    """Interface pour associer un PJ à une campagne"""
    character = CharacterTemplate.query.get_or_404(character_id)

    # Vérifier que c'est bien le propriétaire du PJ
    if character.owner_id != g.current_user.id:
        flash('Vous ne pouvez pas modifier ce personnage.', 'error')
        return redirect(url_for('template.character_profile', id=character_id))

    # Vérifier que c'est un PJ
    if character.character_type != 'PJ':
        flash('Seuls les PJ peuvent rejoindre des campagnes.', 'error')
        return redirect(url_for('template.character_profile', id=character_id))

    # Récupérer les campagnes où l'utilisateur est membre
    available_campaigns = []
    for campaign in g.current_user.get_campaigns():
        # PJ peut rejoindre les campagnes où il est membre (pas MJ)
        if not g.current_user.is_mj_of(campaign):
            available_campaigns.append(campaign)

    if request.method == 'POST':
        campaign_id = request.form.get('campaign_id')

        if not campaign_id:
            flash('Veuillez sélectionner une campagne.', 'error')
        else:
            campaign = Campaign.query.get(campaign_id)

            # Vérifier que l'utilisateur a accès à cette campagne
            if campaign and g.current_user.can_access_campaign(campaign):
                if campaign not in character.campaigns:
                    character.campaigns.append(campaign)
                character.campaign_id = int(campaign_id)
                db.session.commit()

                flash(f'🎉 {character.name} a rejoint la campagne "{campaign.name}" !', 'success')
                return redirect(url_for('template.character_profile', id=character_id))
            else:
                flash('Campagne invalide ou accès interdit.', 'error')

    return render_template('template/join_campaign.html',
                           character=character,
                           campaigns=available_campaigns)
