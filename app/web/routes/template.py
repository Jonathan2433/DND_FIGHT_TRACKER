# Migrated to app.web.routes
"""Routes pour la gestion des templates et personnages"""
import json
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, current_app, jsonify, flash, g
from werkzeug.datastructures import MultiDict
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
from app.utils.spell_catalog import get_cantrips, get_spells_for_level, load_spell_catalog
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


def _resolve_species_speed(species_name, profile_data=None):
    """Retourner la vitesse de déplacement (en pieds) depuis le profil ou l'espèce."""
    if isinstance(profile_data, dict):
        for explicit_key in ('walk_speed', 'movement_speed'):
            explicit_value = profile_data.get(explicit_key)
            if explicit_value not in (None, ''):
                return explicit_value

        raw_speed = profile_data.get('speed')
        if isinstance(raw_speed, dict):
            walk_speed = raw_speed.get('walk')
            if walk_speed not in (None, ''):
                return walk_speed
        elif raw_speed not in (None, ''):
            return raw_speed

    species_rules = get_localized_species_rules()
    if not species_name:
        return None

    normalized_species_name = str(species_name).strip().casefold()
    reverse_labels = {
        str(label).strip().casefold(): key
        for key, label in SPECIES_LABELS_FR.items()
        if label
    }
    candidate_keys = [species_name, reverse_labels.get(normalized_species_name)]

    if normalized_species_name:
        for species_key in species_rules:
            if str(species_key).strip().casefold() == normalized_species_name:
                candidate_keys.append(species_key)
                break

    for candidate in candidate_keys:
        if not candidate:
            continue
        candidate_speed = species_rules.get(candidate, {}).get('speed')
        if candidate_speed not in (None, ''):
            return candidate_speed

    return None


def _extract_choice_selections_by_scope(source):
    """Reconstruit les sélections de choix depuis le bridge JSON du funnel guidé."""
    raw_payload = source.get('feat_choices')
    parsed = _parse_json_payload(raw_payload, default=[])
    grouped = {
        'class': {},
        'species': {},
        'feat': {},
    }
    if not isinstance(parsed, list):
        return grouped

    for entry in parsed:
        if not isinstance(entry, dict):
            continue
        raw_scope = str(entry.get('scope') or '').strip()
        if raw_scope == 'class':
            scope = 'class'
        elif raw_scope == 'species':
            scope = 'species'
        elif raw_scope.startswith('feat_'):
            scope = 'feat'
        else:
            continue

        choice_id = str(entry.get('choice_id') or '').strip()
        value = str(entry.get('value') or '').strip()
        if not choice_id or not value:
            continue
        grouped[scope].setdefault(choice_id, [])
        grouped[scope][choice_id].append(value)

    return grouped


def _extract_spell_selections_by_choice(source):
    """Reconstruit les selections de sorts classees par choice_id depuis le bridge JSON."""
    raw_payload = source.get('feat_choices')
    parsed = _parse_json_payload(raw_payload, default=[])
    spells_by_choice = {}
    spell_choice_types = {'spell', 'cantrip', 'prepared_spell', 'spellbook_entry'}
    if not isinstance(parsed, list):
        return spells_by_choice

    for entry in parsed:
        if not isinstance(entry, dict):
            continue
        scope = str(entry.get('scope') or '').strip()
        if scope not in {'class', 'spell'}:
            continue
        choice_type = str(entry.get('choice_type') or '').strip()
        if choice_type not in spell_choice_types:
            continue
        choice_id = str(entry.get('choice_id') or '').strip()
        value = str(entry.get('value') or '').strip()
        if not choice_id or not value:
            continue
        spells_by_choice.setdefault(choice_id, [])
        spells_by_choice[choice_id].append(value)

    return spells_by_choice


def _extract_builder_state(source):
    getlist = getattr(source, 'getlist', lambda _key: [])
    grouped_choices = _extract_choice_selections_by_scope(source)
    grouped_spells = _extract_spell_selections_by_choice(source)
    raw_selected_spell_ids_by_choice = source.get('selected_spell_ids_by_choice_json')
    raw_selected_spells_by_choice = source.get('selected_spells_by_choice_json')
    parsed_selected_spell_ids_by_choice = _parse_json_payload(raw_selected_spell_ids_by_choice, default=None)
    parsed_selected_spells_by_choice = _parse_json_payload(raw_selected_spells_by_choice, default=None)
    if isinstance(parsed_selected_spell_ids_by_choice, dict):
        selected_spells_payload = parsed_selected_spell_ids_by_choice
    elif isinstance(parsed_selected_spells_by_choice, dict):
        selected_spells_payload = parsed_selected_spells_by_choice
    else:
        selected_spells_payload = grouped_spells
    legacy_ability_field_mapping = {
        'force_base': 'strength',
        'strength_base': 'strength',
        'dexterite_base': 'dexterity',
        'dextérité_base': 'dexterity',
        'dexterity_base': 'dexterity',
        'constitution_base': 'constitution',
        'intelligence_base': 'intelligence',
        'sagesse_base': 'wisdom',
        'wisdom_base': 'wisdom',
        'charisme_base': 'charisma',
        'charisma_base': 'charisma',
    }
    base_ability_scores = _parse_json_payload(
        source.get('base_ability_scores_json') or source.get('base_ability_scores'),
        default={},
    )
    if not isinstance(base_ability_scores, dict):
        base_ability_scores = {}

    for raw_field, canonical_ability in legacy_ability_field_mapping.items():
        raw_value = source.get(raw_field)
        if raw_value in (None, ''):
            continue
        try:
            base_ability_scores[canonical_ability] = int(raw_value)
        except (TypeError, ValueError):
            continue

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
        'base_ability_scores': base_ability_scores,
        'background_ability_bonus_mode': source.get('background_ability_bonus_mode') or None,
        'background_ability_bonus_allocations': _parse_json_payload(
            source.get('background_ability_bonus_allocations_json'),
            default=[item for item in getlist('background_ability_bonus_allocations') if item],
        ),
        'selected_spell_ids_by_choice': selected_spells_payload,
        'selected_equipment_choices_by_slot': _parse_json_payload(source.get('selected_equipment_choices_by_slot_json'), default={}),
        'selected_class_choice_ids': grouped_choices['class'] or [choice_id for choice_id in getlist('selected_class_choice_ids') if choice_id],
        'selected_species_choice_ids': grouped_choices['species'] or [choice_id for choice_id in getlist('selected_species_choice_ids') if choice_id],
        'selected_feat_choice_ids': grouped_choices['feat'] or [choice_id for choice_id in getlist('selected_feat_choice_ids') if choice_id],
    }

    # Aliases legacy uniquement si explicitement fournis afin de ne pas écraser
    # les champs canoniques déjà reconstruits depuis le funnel guidé.
    if source.get('ability_method_id'):
        state['ability_method_id'] = source.get('ability_method_id')
    base_abilities_alias = _parse_json_payload(source.get('base_abilities_json') or source.get('base_abilities'), default={})
    if isinstance(base_abilities_alias, dict) and base_abilities_alias:
        state['base_abilities'] = base_abilities_alias
    if source.get('equipment_choices_by_slot_json'):
        state['equipment_choices_by_slot'] = _parse_json_payload(source.get('equipment_choices_by_slot_json'), default={})
    if source.get('class_choice_ids'):
        state['class_choice_ids'] = grouped_choices['class'] or [choice_id for choice_id in getlist('class_choice_ids') if choice_id]
    if source.get('species_choice_ids'):
        state['species_choice_ids'] = grouped_choices['species'] or [choice_id for choice_id in getlist('species_choice_ids') if choice_id]
    if source.get('feat_choice_ids'):
        state['feat_choice_ids'] = grouped_choices['feat'] or [choice_id for choice_id in getlist('feat_choice_ids') if choice_id]
    if source.get('selected_spells_by_choice_json'):
        state['selected_spells_by_choice'] = selected_spells_payload

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




def _normalize_known_spell_key(value):
    normalized = (
        (value or '')
        .strip()
        .lower()
        .replace("’", "'")
        .replace("`", "'")
        .replace('-', '_')
        .replace(' ', '_')
    )
    if normalized.startswith('ccolor_'):
        return normalized[1:]
    return normalized


def _build_legacy_spell_aliases():
    aliases = {}
    legacy_catalog_path = Path(current_app.root_path) / 'data' / 'spells_catalog.json'
    try:
        payload = json.loads(legacy_catalog_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return aliases

    if not isinstance(payload, list):
        return aliases

    for spell in payload:
        if not isinstance(spell, dict):
            continue

        canonical_key = ''
        for candidate in (spell.get('name_fr'), spell.get('Spell_FR'), spell.get('name'), spell.get('Spell')):
            normalized = _normalize_known_spell_key(candidate)
            if normalized:
                canonical_key = normalized
                break
        if not canonical_key:
            continue

        for alias_candidate in (spell.get('name'), spell.get('Spell'), spell.get('id'), spell.get('name_fr'), spell.get('Spell_FR')):
            alias_key = _normalize_known_spell_key(alias_candidate)
            if alias_key and alias_key not in aliases:
                aliases[alias_key] = canonical_key
    return aliases


def _build_spell_lookup():
    lookup = {}
    for spell in load_spell_catalog():
        if not isinstance(spell, dict):
            continue
        for candidate in (spell.get('name'), spell.get('name_en'), spell.get('id')):
            normalized = _normalize_known_spell_key(candidate)
            if normalized and normalized not in lookup:
                lookup[normalized] = spell

    for alias_key, canonical_key in _build_legacy_spell_aliases().items():
        canonical_spell = lookup.get(canonical_key)
        if canonical_spell and alias_key not in lookup:
            lookup[alias_key] = canonical_spell
    return lookup


def _build_known_spells(character_id, profile):
    cantrips = _split_spell_names(profile.get('selected_cantrips')) if profile else []
    level_one_spells = _split_spell_names(profile.get('selected_level_1_spells')) if profile else []
    known_spells = []
    spell_lookup = _build_spell_lookup()

    def _serialize_known_spell(raw_spell_name, level_label):
        spell_details = spell_lookup.get(_normalize_known_spell_key(raw_spell_name), {})
        display_name = spell_details.get('name') or raw_spell_name
        slug_source = spell_details.get('name') or raw_spell_name
        slug = _slugify_spell_name(slug_source)
        return {
            'name': display_name,
            'level_label': level_label,
            'slug': slug,
            'href': url_for(
                'main.spell_detail',
                spell_slug=slug,
                return_to=url_for('template.character_profile', id=character_id),
                return_label='Retour personnage',
            ),
        }

    for spell_name in cantrips:
        known_spells.append(_serialize_known_spell(spell_name, 'Sort mineur'))

    for spell_name in level_one_spells:
        known_spells.append(_serialize_known_spell(spell_name, 'Niveau 1'))

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
    incoming_payload = request.form.to_dict(flat=False)
    current_app.logger.info("Create character raw form payload: %s", incoming_payload)
    state = _extract_builder_state(request.form)
    current_app.logger.info("Create character normalized builder state: %s", state)
    current_app.logger.info("selected_spell_ids_by_choice=%s", state.get("selected_spell_ids_by_choice"))
    current_app.logger.info("state_snapshot=%s", state)
    current_app.logger.info(
        "Origin bonuses raw payload: %s",
        incoming_payload.get("background_ability_bonus_allocations_json"),
    )
    current_app.logger.info(
        "Origin bonuses normalized payload: %s",
        {
            "mode": state.get("background_ability_bonus_mode"),
            "allocations": state.get("background_ability_bonus_allocations"),
        },
    )
    validation_errors = service.validate_character_creation_submission(state)
    if validation_errors:
        current_app.logger.warning("Create character validator rejection reasons: %s", validation_errors)
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
        current_app.logger.info(
            "CREATE_CHARACTER entrypoint payload snapshot: class_id=%s background_id=%s species_id=%s selected_equipment_ids=%s selected_class_choices=%s selected_species_choices=%s selected_feat_choices=%s",
            state.get("class_id"),
            state.get("background_id"),
            state.get("species_id"),
            state.get("selected_equipment_ids"),
            state.get("selected_class_choice_ids"),
            state.get("selected_species_choice_ids"),
            state.get("selected_feat_choice_ids"),
        )
        created_character = TemplateService.create_character_template(
            request.form,
            request.files,
            current_app.config['UPLOAD_FOLDER'],
            current_user_id=g.current_user.id,
            campaign_id=campaign_id
        )
    except ValueError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('template.manage_templates', campaign_id=campaign_id) if campaign_id else url_for('template.manage_templates'))
    except Exception:
        current_app.logger.exception(
            "CREATE_CHARACTER fatal error during final creation. normalized_state=%s raw_form=%s raw_files=%s",
            state,
            incoming_payload,
            list(request.files.keys()),
        )
        flash(
            "Une erreur interne est survenue pendant la création du personnage. "
            "Merci de réessayer.",
            'error',
        )
        return redirect(url_for('template.manage_templates', campaign_id=campaign_id) if campaign_id else url_for('template.manage_templates'))

    flash(
        f'✅ {created_character.name} bien créé, PDF généré et ajouté dans vos personnages.',
        'success'
    )
    return redirect(url_for('template.character_profile', id=created_character.id))


@bp.route('/character/import-json', methods=['POST'])
@login_required
def import_character_template_json():
    """Importe un export JSON de PJ, cree le personnage et redirige vers son profil."""
    uploaded_file = request.files.get('character_json_file')
    campaign_id = request.form.get('campaign_id', type=int)

    if campaign_id:
        campaign = CampaignService.get_campaign_with_access_check(campaign_id, g.current_user.id)
        if not campaign:
            flash('Campagne invalide ou accès interdit.', 'error')
            return redirect(url_for('template.manage_templates'))

    if not uploaded_file or not uploaded_file.filename:
        flash('Veuillez sélectionner un fichier JSON à importer.', 'error')
        return redirect(url_for('template.manage_templates', campaign_id=campaign_id) if campaign_id else url_for('template.manage_templates'))

    try:
        raw_payload = uploaded_file.read().decode('utf-8')
        parsed_payload = json.loads(raw_payload)
    except (UnicodeDecodeError, json.JSONDecodeError):
        flash('Fichier JSON invalide : impossible de lire le contenu.', 'error')
        return redirect(url_for('template.manage_templates', campaign_id=campaign_id) if campaign_id else url_for('template.manage_templates'))

    character_form_payload = parsed_payload.get('character_form_payload')
    if not isinstance(character_form_payload, dict):
        flash('Fichier JSON invalide : "character_form_payload" manquant.', 'error')
        return redirect(url_for('template.manage_templates', campaign_id=campaign_id) if campaign_id else url_for('template.manage_templates'))

    imported_form_data = MultiDict()
    for key, value in character_form_payload.items():
        if key == 'csrf_token':
            continue
        if isinstance(value, list):
            for item in value:
                imported_form_data.add(key, '' if item is None else str(item))
        else:
            imported_form_data.add(key, '' if value is None else str(value))

    if campaign_id and not imported_form_data.get('campaign_id'):
        imported_form_data.add('campaign_id', str(campaign_id))

    state = _extract_builder_state(imported_form_data)
    validation_errors = get_character_builder_service().validate_character_creation_submission(state)
    if validation_errors:
        flash(f"Import refusé : {' | '.join(validation_errors)}", 'error')
        return redirect(url_for('template.manage_templates', campaign_id=campaign_id) if campaign_id else url_for('template.manage_templates'))

    try:
        created_character = TemplateService.create_character_template(
            imported_form_data,
            MultiDict(),
            current_app.config['UPLOAD_FOLDER'],
            current_user_id=g.current_user.id,
            campaign_id=campaign_id,
        )
    except ValueError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('template.manage_templates', campaign_id=campaign_id) if campaign_id else url_for('template.manage_templates'))
    except Exception:
        current_app.logger.exception(
            "IMPORT_CHARACTER_JSON fatal error. payload_keys=%s state=%s",
            list(character_form_payload.keys()),
            state,
        )
        flash(
            "Une erreur interne est survenue pendant l'import du personnage.",
            'error',
        )
        return redirect(url_for('template.manage_templates', campaign_id=campaign_id) if campaign_id else url_for('template.manage_templates'))

    flash(f'✅ {created_character.name} importé avec succès, PDF généré et personnage créé.', 'success')
    return redirect(url_for('template.character_profile', id=created_character.id))


@bp.route('/character/guided/generate-pdf', methods=['POST'])
def generate_guided_character_pdf():
    """Genere un PDF depuis le funnel guide puis retourne son URL publique."""
    service = get_character_builder_service()
    incoming_payload = request.form.to_dict(flat=False)
    current_app.logger.info("Generate PDF raw form payload: %s", incoming_payload)
    state = _extract_builder_state(request.form)
    current_app.logger.info("Generate PDF normalized builder state: %s", state)
    current_app.logger.info("selected_spell_ids_by_choice=%s", state.get("selected_spell_ids_by_choice"))
    current_app.logger.info("state_snapshot=%s", state)
    current_app.logger.info(
        "Origin bonuses raw payload: %s",
        incoming_payload.get("background_ability_bonus_allocations_json"),
    )
    current_app.logger.info(
        "Origin bonuses normalized payload: %s",
        {
            "mode": state.get("background_ability_bonus_mode"),
            "allocations": state.get("background_ability_bonus_allocations"),
        },
    )
    validation_errors = service.validate_character_creation_submission(state)
    if validation_errors:
        current_app.logger.warning("Generate PDF validator rejection reasons: %s", validation_errors)
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
    except Exception:
        current_app.logger.exception("Unexpected error while generating guided character PDF.")
        return jsonify(
            {
                'ok': False,
                'errors': [
                    "Une erreur interne est survenue pendant la génération du PDF."
                ],
            }
        ), 500

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

    return render_template(
        "edit_character.html",
        character=template,
        dnd_alignments=ALIGNMENTS_FR,
        common_languages=COMMON_LANGUAGES,
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
    species_key = (visible_payload['data'].get('race') if visible_payload else None) or character.race
    speed_value = _resolve_species_speed(species_key, visible_payload['data'] if visible_payload else None)
    known_spells = _build_known_spells(character.id, visible_payload['data'] if visible_payload else {})
    can_award_xp = False
    can_view_xp = False
    is_campaign_mj = False
    show_xp_section = not bool(character.campaign or character.campaigns)
    can_manage_combat_state = _can_manage_character_combat_state(character, current_user)
    active_combat_ids, prioritized_combatant = _get_character_live_combat_context(character.id)

    if current_user:
        can_manage_from_campaigns = any(current_user.is_mj_of(c) for c in character.campaigns)
        is_main_campaign_mj = bool(character.campaign and current_user.is_mj_of(character.campaign))

        is_campaign_mj = is_main_campaign_mj or can_manage_from_campaigns
        can_view_xp = is_campaign_mj
        can_award_xp = is_campaign_mj
        show_xp_section = show_xp_section or is_campaign_mj

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
        show_xp_section=show_xp_section,
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
