"""Routes pour la gestion des combats"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.services import CombatService, CombatantService, GroupService, TemplateService
from app.models import Combat, CharacterTemplate, EncounterTemplate
from app.utils import CONDITIONS_LIST, CONDITIONS_DESCRIPTIONS, MONSTER_TEMPLATES
from app.extensions import socketio

# Créer le blueprint
bp = Blueprint('combat', __name__, url_prefix='/combat')


@bp.route('/create', methods=['POST'])
def create_combat():
    """Créer un nouveau combat"""
    name = request.form['name']
    combat = CombatService.create_combat(name)
    return redirect(url_for('combat.view_combat', combat_id=combat.id))


@bp.route('/<int:combat_id>')
def view_combat(combat_id):
    """Afficher un combat"""
    combat_data = CombatService.get_combat_with_organized_data(combat_id)
    character_templates = CharacterTemplate.query.all()
    encounter_templates = EncounterTemplate.query.all()

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
def view_combat_player(combat_id):
    """Vue joueur pour un combat"""
    from app.utils import get_current_actor

    combat = Combat.query.get_or_404(combat_id)
    combat_data = CombatService.get_combat_with_organized_data(combat_id)

    # Combattants triés par initiative
    combatants_sorted = sorted(
        [c for c in combat.combatants],
        key=lambda x: x.initiative,
        reverse=True
    )

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


@bp.route('/<int:combat_id>/start')
def start_combat(combat_id):
    """Démarrer un combat"""
    CombatService.start_combat(combat_id)
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/next_turn')
def next_turn(combat_id):
    """Passer au tour suivant"""
    CombatService.next_turn(combat_id)
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/close')
def close_combat(combat_id):
    """Clôturer un combat"""
    combat = CombatService.close_combat(combat_id)
    broadcast_combat_update(combat_id)
    return redirect(url_for('summary.combat_summary', combat_id=combat.id))


@bp.route('/<int:combat_id>/add', methods=['POST'])
def add_combatant(combat_id):
    """Ajouter un combattant"""
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
def add_character_template(combat_id):
    """Ajouter un template de personnage au combat"""
    template_id = request.form.get("template_id")
    initiative = int(request.form.get("initiative"))

    TemplateService.add_character_template_to_combat(combat_id, template_id, initiative)
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/load_encounter', methods=['POST'])
def load_encounter(combat_id):
    """Charger un template de rencontre"""
    encounter_id = int(request.form['encounter_id'])
    TemplateService.load_encounter_template(combat_id, encounter_id)
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/add_template', methods=['POST'])
def add_template(combat_id):
    """Ajouter des monstres depuis templates"""
    template_name = request.form['template']
    quantity = int(request.form['quantity'])
    manual_initiative = request.form.get('initiative')

    TemplateService.add_monster_template_to_combat(
        combat_id, template_name, quantity, manual_initiative
    )
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/create_group', methods=['POST'])
def create_group(combat_id):
    """Créer un groupe de combattants"""
    ids = request.form.getlist('selected_combatants')
    GroupService.create_group([int(id) for id in ids])
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:combat_id>/state')
def combat_state(combat_id):
    """État JSON du combat pour synchronisation"""
    from app.utils import get_current_actor

    combat = Combat.query.get_or_404(combat_id)
    combatants = sorted(
        [c for c in combat.combatants if not c.is_hidden],
        key=lambda x: x.initiative,
        reverse=True
    )
    current_actor = get_current_actor(combat)

    return jsonify({
        "round": combat.round,
        "current_actor_id": current_actor.id if current_actor else None,
        "combatants": [
            {
                "id": c.id,
                "name": c.name,
                "type": c.type,
                "hp_current": c.hp_current,
                "hp_max": c.hp_max,
                "temp_hp": c.temp_hp,
                "initiative": c.initiative,
                "ac_total": c.ac_total,
                "is_dead": c.is_dead,
                "has_fled": c.has_fled,
                "conditions": c.conditions.split(",") if c.conditions else [],
                "notes": c.notes
            }
            for c in combatants
        ]
    })


@bp.route('/<int:combat_id>/delete', methods=['POST'])
def delete_combat(combat_id):
    """Supprimer un combat"""
    from app.services import CombatService

    CombatService.delete_combat(combat_id)
    return redirect(url_for('main.index'))


def broadcast_combat_update(combat_id):
    """Diffuser une mise à jour via SocketIO"""
    socketio.emit(
        "combat_update",
        {"combat_id": combat_id},
        room=f"combat_{combat_id}"
    )

