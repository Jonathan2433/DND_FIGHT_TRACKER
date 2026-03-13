"""Routes pour la gestion des combattants individuels."""
from flask import Blueprint, request, redirect, url_for, flash, g

from app.application.use_cases import CombatantService
from app.models import Combatant
from app.utils.decorators import login_required
from app.web.routes.combat import broadcast_combat_update


bp = Blueprint('combatant', __name__, url_prefix='/combatant')


def _can_manage_combatant(combatant):
    combat = combatant.combat
    if g.current_user.role == 'Admin':
        return True
    if combat.campaign:
        return g.current_user.is_mj_of(combat.campaign)
    return g.current_user.has_mj_capability()


def _deny(combat_id):
    flash('Action reservee au MJ proprietaire.', 'error')
    return redirect(url_for('combat.view_combat_player', combat_id=combat_id))


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_combatant(id):
    """Supprimer un combattant."""
    combatant = Combatant.query.get_or_404(id)
    if not _can_manage_combatant(combatant):
        return _deny(combatant.combat_id)

    combat_id = CombatantService.delete_combatant(id)
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:id>/toggle_visibility')
@login_required
def toggle_visibility(id):
    """Basculer la visibilite d'un combattant."""
    combatant = Combatant.query.get_or_404(id)
    if not _can_manage_combatant(combatant):
        return _deny(combatant.combat_id)

    combatant = CombatantService.toggle_visibility(id)
    broadcast_combat_update(combatant.combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combatant.combat_id))


@bp.route('/<int:id>/toggle_fled')
@login_required
def toggle_fled(id):
    """Basculer l'etat de fuite d'un combattant."""
    combatant = Combatant.query.get_or_404(id)
    if not _can_manage_combatant(combatant):
        return _deny(combatant.combat_id)

    combatant = CombatantService.toggle_fled_status(id)
    broadcast_combat_update(combatant.combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combatant.combat_id))


@bp.route('/<int:id>/damage', methods=['POST'])
@login_required
def damage(id):
    """Infliger des degats a un combattant."""
    combatant = Combatant.query.get_or_404(id)
    if not _can_manage_combatant(combatant):
        return _deny(combatant.combat_id)

    amount = int(request.form['amount'])
    combatant = CombatantService.apply_damage(id, amount)
    broadcast_combat_update(combatant.combat.id)
    return redirect(url_for('combat.view_combat', combat_id=combatant.combat.id))


@bp.route('/<int:id>/heal', methods=['POST'])
@login_required
def heal(id):
    """Soigner un combattant."""
    combatant = Combatant.query.get_or_404(id)
    if not _can_manage_combatant(combatant):
        return _deny(combatant.combat_id)

    amount = int(request.form['amount'])
    combatant = CombatantService.apply_heal(id, amount)
    broadcast_combat_update(combatant.combat.id)
    return redirect(url_for('combat.view_combat', combat_id=combatant.combat_id))


@bp.route('/<int:id>/modify_ac', methods=['POST'])
@login_required
def modify_ac(id):
    """Modifier la CA d'un combattant."""
    combatant = Combatant.query.get_or_404(id)
    if not _can_manage_combatant(combatant):
        return _deny(combatant.combat_id)

    amount = int(request.form['amount'])
    combatant = CombatantService.modify_ac(id, amount)
    broadcast_combat_update(combatant.combat.id)
    return redirect(url_for('combat.view_combat', combat_id=combatant.combat.id))


@bp.route('/<int:id>/modify_temp_hp', methods=['POST'])
@login_required
def modify_temp_hp(id):
    """Modifier les PV temporaires d'un combattant."""
    combatant = Combatant.query.get_or_404(id)
    if not _can_manage_combatant(combatant):
        return _deny(combatant.combat_id)

    amount = int(request.form['amount'])
    combatant = CombatantService.modify_temp_hp(id, amount)
    broadcast_combat_update(combatant.combat.id)
    return redirect(url_for('combat.view_combat', combat_id=combatant.combat.id))


@bp.route('/<int:id>/toggle_condition/<condition>')
@login_required
def toggle_condition(id, condition):
    """Basculer une condition sur un combattant."""
    combatant = Combatant.query.get_or_404(id)
    if not _can_manage_combatant(combatant):
        return _deny(combatant.combat_id)

    combatant = CombatantService.toggle_condition(id, condition)
    broadcast_combat_update(combatant.combat.id)
    return redirect(url_for('combat.view_combat', combat_id=combatant.combat.id))
