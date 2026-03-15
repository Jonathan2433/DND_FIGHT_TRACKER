"""Routes pour la gestion des combats"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, g, flash

from app.application.use_cases import CombatService, CombatantService, GroupService, TemplateService
from app.models import Combat, CharacterTemplate, EncounterTemplate
from app.domain.policies import CombatPolicy, EncounterTemplatePolicy
from app.utils import CONDITIONS_LIST, CONDITIONS_DESCRIPTIONS, MONSTER_TEMPLATES, get_initiative_order
from app.utils.decorators import login_required
from app.extensions import socketio


bp = Blueprint('combat', __name__, url_prefix='/combat')


def _can_manage_combat(combat):
    return CombatPolicy.can_manage(g.current_user, combat)


def _can_view_player_combat(combat):
    return CombatPolicy.can_view_player(g.current_user, combat)


@bp.route('/create', methods=['POST'])
@login_required
def create_combat():
    """Creer un nouveau combat rattache a un arc narratif."""
    story_arc_id = request.form.get('story_arc_id')
    episode_id = request.form.get('episode_id')

    if not story_arc_id or not episode_id:
        flash("Un combat doit obligatoirement etre rattache a un arc et un episode.", "error")
        return redirect(url_for('main.index'))

    from app.models.story_arc import StoryArc
    from app.models.episode import Episode

    arc = StoryArc.query.get_or_404(int(story_arc_id))
    episode = Episode.query.get_or_404(int(episode_id))
    if episode.story_arc_id != arc.id:
        flash("Episode invalide pour cet arc narratif.", "error")
        return redirect(url_for('campaign.view_campaign', campaign_id=arc.campaign_id))
    if not (g.current_user.role == 'Admin' or g.current_user.is_mj_of(arc.campaign)):
        flash("Seul le MJ proprietaire peut creer un combat sur cet arc.", "error")
        return redirect(url_for('campaign.view_campaign', campaign_id=arc.campaign_id))

    name = request.form['name']
    combat = CombatService.create_combat(
        name=name,
        story_arc_id=arc.id,
        campaign_id=arc.campaign_id,
        episode_id=episode.id,
    )

    return redirect(url_for('combat.view_combat', combat_id=combat.id))


@bp.route('/<int:combat_id>')
@login_required
def view_combat(combat_id):
    """Afficher un combat (vue MJ)."""
    combat = Combat.query.get_or_404(combat_id)
    if not _can_manage_combat(combat):
        flash('Seul le MJ proprietaire peut acceder a la gestion du combat.', 'error')
        return redirect(url_for('combat.view_combat_player', combat_id=combat_id))

    combat_data = CombatService.get_combat_with_organized_data(combat_id)
    character_templates = CharacterTemplate.query.all()
    if g.current_user.role == 'Admin':
        encounter_templates = EncounterTemplate.query.all()
    else:
        encounter_templates = EncounterTemplate.query.filter_by(owner_id=g.current_user.id).all()

    return render_template(
        'combat.html',
        combat=combat_data['combat'],
        groups=combat_data['groups'],
        singles=combat_data['singles'],
        group_condition_states=combat_data['group_condition_states'],
        conditions_list=CONDITIONS_LIST,
        conditions_descriptions=CONDITIONS_DESCRIPTIONS,
        MONSTER_TEMPLATES=MONSTER_TEMPLATES,
        character_templates=character_templates,
        encounter_templates=encounter_templates,
        start_time=combat_data['combat'].start_time,
        round_start=combat_data['combat'].current_round_start,
        turn_start=combat_data['combat'].current_turn_start,
        initiative_order=combat_data['initiative_order']
    )


@bp.route('/<int:combat_id>/player')
@login_required
def view_combat_player(combat_id):
    """Vue joueur pour un combat."""
    from app.utils import get_current_actor

    combat = Combat.query.get_or_404(combat_id)
    if not _can_view_player_combat(combat):
        flash('Acces non autorise a ce combat.', 'error')
        return redirect(url_for('main.index'))

    combat_data = CombatService.get_combat_with_organized_data(combat_id)
    combatants_sorted = get_initiative_order(combat.combatants)
    current_actor = get_current_actor(combat)

    return render_template(
        'combat_player.html',
        combat=combat,
        combatants=combatants_sorted,
        current_actor=current_actor,
        start_time=combat.start_time,
        round_start=combat.current_round_start,
        turn_start=combat.current_turn_start,
        groups=combat_data['groups'],
        singles=combat_data['singles'],
        group_condition_states=combat_data['group_condition_states']
    )


def _require_manage_or_redirect(combat_id):
    combat = Combat.query.get_or_404(combat_id)
    if _can_manage_combat(combat):
        return None
    flash('Action reservee au MJ proprietaire.', 'error')
    return redirect(url_for('combat.view_combat_player', combat_id=combat_id))


@bp.route('/<int:combat_id>/start')
@login_required
def start_combat(combat_id):
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    CombatService.start_combat(combat_id)
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/next_turn')
@login_required
def next_turn(combat_id):
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    CombatService.next_turn(combat_id)
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/close')
@login_required
def close_combat(combat_id):
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    combat = CombatService.close_combat(combat_id)
    broadcast_combat_update(combat_id)
    return redirect(url_for('summary.combat_summary', combat_id=combat.id))


@bp.route('/<int:combat_id>/add', methods=['POST'])
@login_required
def add_combatant(combat_id):
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    CombatantService.add_combatant(
        combat_id=combat_id,
        name=request.form['name'],
        type=request.form['type'],
        hp_max=int(request.form['hp_max']),
        hp_current=request.form.get('hp_current'),
        initiative=int(request.form['initiative']),
        ac_base=int(request.form['ac'])
    )
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/add_character_template', methods=['POST'])
@login_required
def add_character_template(combat_id):
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    template_id = request.form.get('template_id')
    initiative = int(request.form.get('initiative'))

    TemplateService.add_character_template_to_combat(combat_id, template_id, initiative)
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/load_encounter', methods=['POST'])
@login_required
def load_encounter(combat_id):
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    encounter_id = int(request.form['encounter_id'])
    encounter = EncounterTemplate.query.get_or_404(encounter_id)
    if not EncounterTemplatePolicy.can_manage(g.current_user, encounter):
        flash('Template de rencontre non autorise.', 'error')
        return redirect(url_for('combat.view_combat', combat_id=combat_id))

    TemplateService.load_encounter_template(combat_id, encounter_id)
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/add_template', methods=['POST'])
@login_required
def add_template(combat_id):
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    template_name = request.form['template']
    quantity = int(request.form['quantity'])
    manual_initiative = request.form.get('initiative')

    TemplateService.add_monster_template_to_combat(
        combat_id,
        template_name,
        quantity,
        manual_initiative
    )
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/create_group', methods=['POST'])
@login_required
def create_group(combat_id):
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    ids = request.form.getlist('selected_combatants')
    GroupService.create_group([int(combatant_id) for combatant_id in ids])
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/state')
@login_required
def combat_state(combat_id):
    """Etat JSON du combat pour synchronisation."""
    from app.utils import get_current_actor

    combat = Combat.query.get_or_404(combat_id)
    if not _can_view_player_combat(combat):
        return jsonify({'error': 'forbidden'}), 403

    combatants = get_initiative_order(combat.combatants)
    current_actor = get_current_actor(combat)

    return jsonify({
        'round': combat.round,
        'current_actor_id': current_actor.id if current_actor else None,
        'combatants': [
            {
                'id': c.id,
                'name': c.name,
                'type': c.type,
                'hp_current': c.hp_current,
                'hp_max': c.hp_max,
                'temp_hp': c.temp_hp,
                'initiative': c.initiative,
                'ac_total': c.ac_total,
                'is_dead': c.is_dead,
                'has_fled': c.has_fled,
                'conditions': c.conditions.split(',') if c.conditions else [],
                'notes': c.notes
            }
            for c in combatants
        ]
    })


@bp.route('/<int:combat_id>/delete', methods=['POST'])
@login_required
def delete_combat(combat_id):
    """Supprimer un combat."""
    redirect_response = _require_manage_or_redirect(combat_id)
    if redirect_response:
        return redirect_response

    CombatService.delete_combat(combat_id)
    return redirect(url_for('main.index'))


def broadcast_combat_update(combat_id):
    """Diffuser une mise a jour via SocketIO."""
    socketio.emit(
        'combat_update',
        {'combat_id': combat_id},
        room=f'combat_{combat_id}'
    )
