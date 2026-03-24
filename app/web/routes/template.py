# Migrated to app.web.routes
"""Routes pour la gestion des templates et personnages"""
import json
from flask import Blueprint, render_template, request, redirect, url_for, current_app, jsonify, flash, g
from app.application.use_cases import TemplateService
from app.application.use_cases.campaign_service import CampaignService
from app.models import CharacterTemplate, EncounterTemplate, Combatant, CombatLog
from app.domain.policies import EncounterTemplatePolicy
from app.utils.decorators import login_required
from app.models.campaign import Campaign
from app.extensions import db
from app.utils.dnd5_rules import (
    RACE_BONUSES,
    CLASS_RULES,
    CLASS_LABELS_FR,
    SPECIES_LABELS_FR,
    BACKGROUND_LABELS_FR,
    ALIGNMENTS_FR,
    STANDARD_ARRAY,
    get_localized_class_rules,
    get_localized_background_rules,
    get_localized_species_rules,
    COMMON_LANGUAGES,
    SPECIES_RULES,
    BACKGROUND_RULES,
    AIDEDED_SKILL_OPTIONS,
    AIDEDED_SPECIES_OPTIONS,
    AIDEDED_CLASS_OPTIONS,
    AIDEDED_BACKGROUND_OPTIONS,
)
from app.utils.spell_catalog import get_cantrips, get_spells_for_level
from app.utils.character_builder_engine import get_rules_loaders, SpellResolverService
from app.services.character_builder_service import get_character_builder_service
from app.web.routes.main import _slugify_spell_name

# Créer le blueprint
bp = Blueprint('template', __name__, url_prefix='/template')


def _extract_items(payload):
    if isinstance(payload, dict):
        candidates = payload.get('items')
        if isinstance(candidates, list):
            return [entry for entry in candidates if isinstance(entry, dict)]
    if isinstance(payload, list):
        return [entry for entry in payload if isinstance(entry, dict)]
    return []


def _entry_label(entry):
    return (
        entry.get('name_fr')
        or entry.get('name')
        or entry.get('label_fr')
        or entry.get('label')
        or entry.get('id')
        or ''
    )


def _entry_description(entry):
    description = entry.get('description_fr') or entry.get('description')
    if description:
        return description
    summary = entry.get('summary_fr') or entry.get('summary')
    return summary or ''


def _serialize_catalog(entries):
    serialized = []
    for entry in entries:
        entry_id = entry.get('id') or entry.get('name')
        if not entry_id:
            continue
        serialized.append(
            {
                'id': entry_id,
                'label': _entry_label(entry),
                'description': _entry_description(entry),
                'raw': entry,
            }
        )
    return serialized


def _resolve_step_order(loaders):
    default_steps = [
        {'id': 'class', 'label': 'Classe'},
        {'id': 'background', 'label': 'Historique'},
        {'id': 'species', 'label': 'Espèce'},
        {'id': 'abilities', 'label': 'Caractéristiques'},
        {'id': 'class_choices', 'label': 'Choix de classe'},
        {'id': 'species_choices', 'label': 'Choix d’espèce'},
        {'id': 'origin_feat', 'label': 'Don d’origine'},
        {'id': 'proficiencies_languages', 'label': 'Compétences & Langues'},
        {'id': 'equipment', 'label': 'Équipement'},
        {'id': 'spellcasting', 'label': 'Incantation'},
        {'id': 'identity', 'label': 'Identité finale'},
    ]
    rules = loaders.character_creation_rules
    if not isinstance(rules, dict):
        return default_steps

    raw_steps = rules.get('steps')
    if not isinstance(raw_steps, list):
        return default_steps

    resolved = []
    for step in raw_steps:
        if not isinstance(step, dict):
            continue
        step_id = step.get('id') or step.get('step_id') or step.get('name')
        if not step_id:
            continue
        resolved.append(
            {
                'id': str(step_id),
                'label': step.get('title_fr') or step.get('title') or step.get('label') or str(step_id),
                'description': step.get('description_fr') or step.get('description') or '',
            }
        )
    return resolved or default_steps


def _parse_json_payload(raw_value, default):
    if not raw_value:
        return default
    try:
        parsed = json.loads(raw_value)
    except (TypeError, ValueError):
        return default
    return parsed


def _extract_builder_state(source):
    getlist = getattr(source, 'getlist', lambda _key: [])
    state = {
        'class_id': source.get('class_id') or None,
        'background_id': source.get('background_id') or None,
        'species_id': source.get('species_id') or None,
        'language_ids': [lang for lang in getlist('language_ids') if lang],
        'selected_language_ids': [lang for lang in getlist('selected_language_ids') if lang],
        'selected_origin_feat_id': source.get('selected_origin_feat_id') or None,
        'selected_feat_ids': [feat for feat in getlist('selected_feat_ids') if feat],
        'selected_equipment_ids': [item for item in getlist('selected_equipment_ids') if item],
        'selected_ability_bonus_ids': [ability for ability in getlist('selected_ability_bonus_ids') if ability],
        'ability_score_method': source.get('ability_score_method') or None,
        'ability_method_id': source.get('ability_method_id') or None,
        'base_ability_scores': _parse_json_payload(source.get('base_ability_scores_json') or source.get('base_ability_scores'), default={}),
        'base_abilities': _parse_json_payload(source.get('base_abilities_json') or source.get('base_abilities'), default={}),
        'background_ability_bonus_mode': source.get('background_ability_bonus_mode') or None,
        'background_ability_bonus_allocations': _parse_json_payload(
            source.get('background_ability_bonus_allocations_json'),
            default=[item for item in getlist('background_ability_bonus_allocations') if item],
        ),
        'selected_spell_ids_by_choice': _parse_json_payload(source.get('selected_spell_ids_by_choice_json'), default={}),
        'selected_spells_by_choice': _parse_json_payload(source.get('selected_spells_by_choice_json'), default={}),
        'selected_equipment_choices_by_slot': _parse_json_payload(source.get('selected_equipment_choices_by_slot_json'), default={}),
        'equipment_choices_by_slot': _parse_json_payload(source.get('equipment_choices_by_slot_json'), default={}),
        'selected_class_choice_ids': [choice_id for choice_id in getlist('selected_class_choice_ids') if choice_id],
        'class_choice_ids': [choice_id for choice_id in getlist('class_choice_ids') if choice_id],
        'selected_species_choice_ids': [choice_id for choice_id in getlist('selected_species_choice_ids') if choice_id],
        'species_choice_ids': [choice_id for choice_id in getlist('species_choice_ids') if choice_id],
        'selected_feat_choice_ids': [choice_id for choice_id in getlist('selected_feat_choice_ids') if choice_id],
        'feat_choice_ids': [choice_id for choice_id in getlist('feat_choice_ids') if choice_id],
    }
    return get_character_builder_service().normalize_character_creation_state(state)


def _can_manage_character_combat_state(character, user):
    """Seul le proprietaire du PJ ou le MJ proprietaire de sa campagne peut modifier HP/CA."""
    if not user or character.character_type != 'PJ':
        return False

    if character.owner_id == user.id:
        return True

    if character.campaign and user.is_mj_of(character.campaign):
        return True

    return any(user.is_mj_of(campaign) for campaign in character.campaigns)


def _get_character_live_combat_context(character_id):
    """Retourne les combats actifs lies a un personnage + le combattant prioritaire."""
    linked_combatants = (
        Combatant.query
        .join(Combatant.combat)
        .filter(
            Combatant.character_template_id == character_id,
            Combatant.combat.has(is_closed=False)
        )
        .all()
    )

    if not linked_combatants:
        return [], None

    def sort_key(combatant):
        combat = combatant.combat
        started_rank = 0 if combat.has_started else 1
        started_at = combat.start_time or combat.created_at
        return (started_rank, started_at)

    ordered = sorted(linked_combatants, key=sort_key, reverse=False)
    combat_ids = [combatant.combat_id for combatant in ordered]
    return combat_ids, ordered[0]


def _split_spell_names(raw_spells):
    return [spell.strip() for spell in (raw_spells or '').split(',') if spell.strip()]


def _build_known_spells(character_id, profile):
    cantrips = _split_spell_names(profile.get('selected_cantrips')) if profile else []
    level_one_spells = _split_spell_names(profile.get('selected_level_1_spells')) if profile else []
    known_spells = []

    for spell_name in cantrips:
        known_spells.append({
            'name': spell_name,
            'level_label': 'Sort mineur',
            'slug': _slugify_spell_name(spell_name),
            'href': url_for(
                'main.spell_detail',
                spell_slug=_slugify_spell_name(spell_name),
                return_to=url_for('template.character_profile', id=character_id),
                return_label='Retour personnage',
            ),
        })

    for spell_name in level_one_spells:
        known_spells.append({
            'name': spell_name,
            'level_label': 'Niveau 1',
            'slug': _slugify_spell_name(spell_name),
            'href': url_for(
                'main.spell_detail',
                spell_slug=_slugify_spell_name(spell_name),
                return_to=url_for('template.character_profile', id=character_id),
                return_label='Retour personnage',
            ),
        })

    return known_spells


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
    pnj_campaign_context = None
    campaign_id = request.args.get('campaign_id', type=int)
    if campaign_id:
        campaign_context = CampaignService.get_campaign_with_access_check(campaign_id, g.current_user.id)
        if not campaign_context:
            flash('Campagne invalide ou accès interdit.', 'error')
            return redirect(url_for('template.manage_templates'))

    if campaign_context and g.current_user.is_mj_of(campaign_context):
        pnj_campaign_context = campaign_context
    else:
        pnj_campaign_context = (
            Campaign.query.filter_by(mj_id=g.current_user.id, is_active=True)
            .order_by(Campaign.created_at.desc())
            .first()
        )

    can_create_pnj = bool(pnj_campaign_context and g.current_user.has_mj_capability())

    return render_template(
        'templates_manager.html',
        characters=characters,
        pj_characters=pj_characters,
        other_characters=other_characters,
        encounters=encounters,
        campaign_context=campaign_context,
        pnj_campaign_context=pnj_campaign_context,
        dnd_species=sorted(RACE_BONUSES.keys()),
        dnd_species_catalog=sorted(SPECIES_RULES.keys()),
        dnd_classes=sorted(CLASS_RULES.keys()),
        dnd_classes_catalog=sorted(CLASS_RULES.keys()),
        dnd_class_labels=CLASS_LABELS_FR,
        dnd_species_labels=SPECIES_LABELS_FR,
        dnd_background_labels=BACKGROUND_LABELS_FR,
        dnd_class_descriptions={name: rule.get('description', '') for name, rule in CLASS_RULES.items()},
        dnd_class_rules=get_localized_class_rules(),
        standard_array=STANDARD_ARRAY,
        dnd_backgrounds=get_localized_background_rules(),
        dnd_background_catalog=sorted(BACKGROUND_RULES.keys()),
        dnd_skill_options=AIDEDED_SKILL_OPTIONS,
        dnd_species_rules=get_localized_species_rules(),
        dnd_alignments=ALIGNMENTS_FR,
        common_languages=COMMON_LANGUAGES,
        cantrip_catalog=get_cantrips(),
        level_one_spell_catalog=get_spells_for_level(1),
        can_create_pnj=can_create_pnj,
    )


@bp.route('/character/create-guided', methods=['GET'])
def create_character_template_guided():
    """Funnel de creation JSON-first, independant du builder historique."""
    service = get_character_builder_service()
    loaders = get_rules_loaders()
    if not loaders.has_knowledge_base():
        flash("La base JSON app/data/DND_RULES_JSON est introuvable.", 'error')
        return redirect(url_for('template.manage_templates'))

    return render_template(
        'character_creation_guided.html',
        dnd_rules_context={
            'steps': service.get_step_definitions(),
            'classes': service.get_available_classes(),
            'backgrounds': service.get_available_backgrounds(),
            'species': service.get_available_species(),
        },
    )


@bp.route('/api/character-builder/funnel-payload', methods=['GET'])
def character_builder_funnel_payload():
    """Retourne les options filtrees selon l'etat courant du builder."""
    service = get_character_builder_service()
    state = _extract_builder_state(request.args)

    payload = {
        'state': state,
        'steps': service.get_step_definitions(),
        'class_payload': service.get_class_payload(state['class_id'], state) if state['class_id'] else {},
        'background_payload': service.get_background_payload(state['background_id'], state) if state['background_id'] else {},
        'species_payload': service.get_species_payload(state['species_id'], state) if state['species_id'] else {},
        'languages_payload': service.get_language_payload(state),
        'ability_payload': service.get_ability_score_payload(state),
        'builder_output': service.build_character_output(state),
    }
    return jsonify(payload)


@bp.route('/api/character-builder/spells', methods=['GET'])
def character_builder_spell_options():
    """Expose les sorts autorises par classe en priorisant spells_by_class.json."""
    class_name = request.args.get('class_name', '')
    level = request.args.get('level', type=int, default=0)
    resolver = SpellResolverService(get_rules_loaders())
    spells = resolver.get_spells_for_class_level(class_name, level)
    output = [
        {
            'id': entry.get('id') or entry.get('name'),
            'name': entry.get('name_fr') or entry.get('name') or entry.get('id'),
            'description': entry.get('description') or '',
            'level': entry.get('level', level),
            'school': entry.get('school') or '',
        }
        for entry in spells
    ]
    return jsonify({'spells': output})


@bp.route('/character/create', methods=['POST'])
def create_character_template():
    """Créer un template de personnage"""
    service = get_character_builder_service()
    validation_errors = service.validate_character_creation_submission(_extract_builder_state(request.form))
    if validation_errors:
        return jsonify({'ok': False, 'errors': validation_errors}), 400

    if not g.current_user:
        flash(
            "Mode test activé : création guidée accessible sans connexion, "
            "mais aucun personnage n'a été enregistré.",
            'info'
        )
        return redirect(url_for('template.create_character_template_guided'))

    campaign_id = request.form.get('campaign_id', type=int)

    if campaign_id:
        campaign = CampaignService.get_campaign_with_access_check(campaign_id, g.current_user.id)
        if not campaign:
            flash('Campagne invalide ou accès interdit.', 'error')
            return redirect(url_for('template.manage_templates'))

    try:
        TemplateService.create_character_template(
            request.form,
            request.files,
            current_app.config['UPLOAD_FOLDER'],
            current_user_id=g.current_user.id,
            campaign_id=campaign_id
        )
    except ValueError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('template.manage_templates', campaign_id=campaign_id) if campaign_id else url_for('template.manage_templates'))

    if campaign_id:
        flash('PJ créé et automatiquement associé à la campagne.', 'success')
        return redirect(url_for('campaign.view_campaign', campaign_id=campaign_id))

    return redirect(url_for('template.manage_templates'))


@bp.route('/character/guided/generate-pdf', methods=['POST'])
def generate_guided_character_pdf():
    """Genere un PDF depuis le funnel guide puis retourne son URL publique."""
    service = get_character_builder_service()
    validation_errors = service.validate_character_creation_submission(_extract_builder_state(request.form))
    if validation_errors:
        return jsonify({'ok': False, 'errors': validation_errors}), 400

    current_user = getattr(g, 'current_user', None)
    try:
        pdf_filename = TemplateService.generate_character_sheet_preview_pdf(
            request.form,
            current_app.config['UPLOAD_FOLDER'],
            current_user=current_user,
        )
    except ValueError as exc:
        return jsonify({'ok': False, 'errors': [str(exc)]}), 400

    return jsonify(
        {
            'ok': True,
            'pdf_filename': pdf_filename,
            'pdf_url': url_for('static', filename=f'uploads/{pdf_filename}'),
        }
    )


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
        try:
            TemplateService.update_character_template(
                id,
                request.form,
                request.files,
                current_app.config['UPLOAD_FOLDER']
            )
        except ValueError as exc:
            flash(str(exc), 'error')
            return redirect(url_for('template.edit_character_template', id=id))

        flash('Personnage modifié avec succès !', 'success')
        return redirect(url_for('template.character_profile', id=id))

    equipment_fields = TemplateService.split_builder_equipment(template.equipment)
    background_fields = TemplateService.split_background_payload(template.background_story)
    selected_skills = {
        token.strip() for token in (template.skill_proficiencies or '').split(',') if token.strip()
    }
    selected_cantrips = {
        token.strip() for token in (template.selected_cantrips or '').split(',') if token.strip()
    }
    selected_level_one_spells = {
        token.strip() for token in (template.selected_level_1_spells or '').split(',') if token.strip()
    }

    return render_template(
        "edit_character.html",
        character=template,
        dnd_species_catalog=AIDEDED_SPECIES_OPTIONS,
        dnd_classes_catalog=AIDEDED_CLASS_OPTIONS,
        dnd_background_catalog=AIDEDED_BACKGROUND_OPTIONS,
        dnd_alignments=ALIGNMENTS_FR,
        common_languages=COMMON_LANGUAGES,
        dnd_skill_options=AIDEDED_SKILL_OPTIONS,
        equipment_fields=equipment_fields,
        background_fields=background_fields,
        selected_skills=selected_skills,
        selected_cantrips=selected_cantrips,
        selected_level_one_spells=selected_level_one_spells,
        cantrip_catalog=get_cantrips(),
        level_one_spell_catalog=get_spells_for_level(1),
    )


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


@bp.route('/character/<int:id>/generate_pdf', methods=['POST'])
@login_required
def generate_character_pdf(id):
    """Generer/re-generer la fiche PDF officielle depuis les donnees stockees."""
    template = CharacterTemplate.query.get_or_404(id)

    if not template.can_be_edited_by(g.current_user):
        flash('Vous n\'etes pas autorise a generer la fiche PDF pour ce personnage.', 'error')
        return redirect(url_for('template.character_profile', id=id))

    try:
        TemplateService.generate_character_sheet_pdf(id, current_app.config['UPLOAD_FOLDER'])
    except ValueError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('template.character_profile', id=id))

    flash('Fiche PDF generee avec succes.', 'success')
    return redirect(url_for('template.character_profile', id=id))


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
    total_damage_dealt = (
        db.session.query(db.func.coalesce(db.func.sum(CombatLog.value), 0))
        .join(Combatant, Combatant.id == CombatLog.actor_id)
        .filter(
            Combatant.character_template_id == character.id,
            CombatLog.action_type == 'damage',
        )
        .scalar()
    ) or 0
    species_rules = get_localized_species_rules()
    species_key = (visible_payload['data'].get('race') if visible_payload else None) or character.race
    speed_value = species_rules.get(species_key, {}).get('speed')
    known_spells = _build_known_spells(character.id, visible_payload['data'] if visible_payload else {})
    can_award_xp = False
    can_view_xp = False
    is_campaign_mj = False
    can_manage_combat_state = _can_manage_character_combat_state(character, current_user)
    active_combat_ids, prioritized_combatant = _get_character_live_combat_context(character.id)

    if current_user:
        is_admin = current_user.role == 'Admin'
        can_manage_from_campaigns = any(current_user.is_mj_of(c) for c in character.campaigns)
        is_main_campaign_mj = bool(character.campaign and current_user.is_mj_of(character.campaign))

        is_campaign_mj = is_main_campaign_mj or can_manage_from_campaigns

        if is_admin:
            can_view_xp = True
            can_award_xp = True
        elif is_campaign_mj:
            can_view_xp = is_campaign_mj
            can_award_xp = is_campaign_mj

    return render_template(
        'character_profile.html',
        character=character,
        visible_character=visible_payload['data'] if visible_payload else None,
        visibility_mode=visibility_mode,
        limited_profile=limited_profile,
        combats_played=combats_played,
        total_damage_dealt=total_damage_dealt,
        speed_value=speed_value,
        known_spells=known_spells,
        can_edit=character.can_be_edited_by(current_user) if current_user else False,
        can_view_xp=can_view_xp,
        can_award_xp=can_award_xp,
        is_campaign_mj=is_campaign_mj,
        can_manage_combat_state=can_manage_combat_state,
        active_combat_ids=active_combat_ids,
        active_combatant=prioritized_combatant,
    )


@bp.route('/character/<int:id>/combat_state', methods=['POST'])
@login_required
def update_character_combat_state(id):
    """Ajuster rapidement les HP/CA persistants d'un PJ."""
    character = CharacterTemplate.query.get_or_404(id)

    if not _can_manage_character_combat_state(character, g.current_user):
        flash('Seul le proprietaire du PJ ou le MJ proprietaire de la campagne peut modifier ces valeurs.', 'error')
        return redirect(url_for('template.character_profile', id=id))

    hp_delta = request.form.get('hp_delta', default=0, type=int) or 0
    temp_hp_delta = request.form.get('temp_hp_delta', default=0, type=int) or 0
    ac_delta = request.form.get('ac_delta', default=0, type=int) or 0

    if hp_delta == 0 and temp_hp_delta == 0 and ac_delta == 0:
        flash('Aucun changement applique (HP, PV temporaires et CA a 0).', 'info')
        return redirect(url_for('template.character_profile', id=id))

    current_hp = character.hp_current_effective
    character.hp_current = max(0, min(current_hp + hp_delta, character.hp_max))
    character.temp_hp = max(0, (character.temp_hp or 0) + temp_hp_delta)
    character.ac_bonus = (character.ac_bonus or 0) + ac_delta

    db.session.commit()

    flash(
        f'Valeurs mises a jour : HP {character.hp_current}/{character.hp_max}, '
        f'PV temporaires {character.temp_hp}, CA {character.ac_total} '
        f'(base {character.ac_base}, bonus/malus temp {character.ac_bonus or 0}).',
        'success'
    )
    return redirect(url_for('template.character_profile', id=id))


@bp.route('/character/<int:id>/live_state', methods=['GET'])
def character_live_state(id):
    """Expose l'etat de combat live d'un personnage (si en combat actif)."""
    character = CharacterTemplate.query.get_or_404(id)

    from flask import session
    from app.application.use_cases.auth_service import AuthService

    current_user = None
    if 'user_id' in session:
        current_user = AuthService.get_user_by_id(session['user_id'])

    if not character.can_be_viewed_by(current_user):
        return jsonify({'error': 'forbidden'}), 403

    active_combat_ids, prioritized_combatant = _get_character_live_combat_context(character.id)
    if not prioritized_combatant:
        return jsonify({
            'has_active_combat': False,
            'active_combat_ids': [],
        })

    return jsonify({
        'has_active_combat': True,
        'active_combat_ids': active_combat_ids,
        'combat_id': prioritized_combatant.combat_id,
        'combat_name': prioritized_combatant.combat.name,
        'combat_round': prioritized_combatant.combat.round,
        'hp_current': prioritized_combatant.hp_current,
        'hp_max': prioritized_combatant.hp_max,
        'temp_hp': prioritized_combatant.temp_hp,
        'ac_total': prioritized_combatant.ac_total,
        'is_dead': prioritized_combatant.is_dead,
        'has_fled': prioritized_combatant.has_fled,
    })


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
    """Interface pour associer un personnage à une campagne"""
    character = CharacterTemplate.query.get_or_404(character_id)

    # Vérifier que c'est bien le propriétaire du PJ
    if character.owner_id != g.current_user.id:
        flash('Vous ne pouvez pas modifier ce personnage.', 'error')
        return redirect(url_for('template.character_profile', id=character_id))

    if character.character_type not in ['PJ', 'PNJ']:
        flash('Ce type de personnage ne peut pas etre associe a une campagne.', 'error')
        return redirect(url_for('template.character_profile', id=character_id))

    if character.character_type == 'PNJ':
        available_campaigns = Campaign.query.filter_by(
            mj_id=g.current_user.id,
            is_active=True,
        ).order_by(Campaign.created_at.desc()).all()
    else:
        available_campaigns = []
        for campaign in g.current_user.get_campaigns():
            if g.current_user.is_mj_of(campaign) or g.current_user.is_member_of(campaign):
                available_campaigns.append(campaign)

    if request.method == 'POST':
        campaign_id = request.form.get('campaign_id', type=int)

        if not campaign_id:
            flash('Veuillez sélectionner une campagne.', 'error')
        else:
            campaign = Campaign.query.get(campaign_id)
            allowed_campaign_ids = {c.id for c in available_campaigns}

            if campaign and campaign.id in allowed_campaign_ids:
                if campaign not in character.campaigns:
                    character.campaigns.append(campaign)
                character.campaign_id = campaign_id
                db.session.commit()

                flash(f'🎉 {character.name} est maintenant associe a la campagne "{campaign.name}" !', 'success')
                return redirect(url_for('template.character_profile', id=character_id))
            else:
                flash('Campagne invalide ou accès interdit.', 'error')

    return render_template('template/join_campaign.html',
                           character=character,
                           campaigns=available_campaigns)
