"""Routes pour la gestion des groupes de combattants."""
from flask import Blueprint, request, redirect, url_for, flash, g

from app.application.use_cases import GroupService
from app.models import Combatant
from app.utils.decorators import login_required


bp = Blueprint('group', __name__, url_prefix='/group')


def _resolve_combat_id(group_id):
    member = Combatant.query.filter_by(group_id=group_id).first()
    return member.combat_id if member else None


def _can_manage_group(group_id):
    member = Combatant.query.filter_by(group_id=group_id).first()
    if not member:
        return False
    combat = member.combat
    if g.current_user.role == 'Admin':
        return True
    if combat.campaign:
        return g.current_user.is_mj_of(combat.campaign)
    return g.current_user.has_mj_capability()


def _deny(group_id):
    combat_id = _resolve_combat_id(group_id)
    flash('Action reservee au MJ proprietaire.', 'error')
    if combat_id:
        return redirect(url_for('combat.view_combat_player', combat_id=combat_id))
    return redirect(url_for('main.index'))


@bp.route('/<int:group_id>/ungroup')
@login_required
def ungroup(group_id):
    """Defaire un groupe."""
    if not _can_manage_group(group_id):
        return _deny(group_id)

    combat_id = GroupService.ungroup(group_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:group_id>/damage', methods=['POST'])
@login_required
def damage_group(group_id):
    """Infliger des degats a un groupe."""
    if not _can_manage_group(group_id):
        return _deny(group_id)

    amount = int(request.form['amount'])
    combat_id = GroupService.apply_group_damage(group_id, amount)

    from app.web.routes.combat import broadcast_combat_update
    broadcast_combat_update(combat_id)

    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:group_id>/heal', methods=['POST'])
@login_required
def heal_group(group_id):
    """Soigner un groupe."""
    if not _can_manage_group(group_id):
        return _deny(group_id)

    amount = int(request.form['amount'])
    combat_id = GroupService.apply_group_heal(group_id, amount)

    from app.web.routes.combat import broadcast_combat_update
    broadcast_combat_update(combat_id)

    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:group_id>/toggle_condition/<condition>')
@login_required
def toggle_condition_group(group_id, condition):
    """Basculer une condition sur un groupe."""
    if not _can_manage_group(group_id):
        return _deny(group_id)

    combat_id = GroupService.toggle_group_condition(group_id, condition)

    from app.web.routes.combat import broadcast_combat_update
    broadcast_combat_update(combat_id)

    return redirect(url_for('combat.view_combat', combat_id=combat_id))
