"""Routes pour la gestion des groupes de combattants"""
from flask import Blueprint, request, redirect, url_for
from app.services import GroupService

# Créer le blueprint
bp = Blueprint('group', __name__, url_prefix='/group')


@bp.route('/<int:group_id>/ungroup')
def ungroup(group_id):
    """Défaire un groupe"""
    combat_id = GroupService.ungroup(group_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:group_id>/damage', methods=['POST'])
def damage_group(group_id):
    """Infliger des dégâts à un groupe"""
    amount = int(request.form['amount'])
    combat_id = GroupService.apply_group_damage(group_id, amount)

    from app.routes.combat import broadcast_combat_update
    broadcast_combat_update(combat_id)

    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:group_id>/heal', methods=['POST'])
def heal_group(group_id):
    """Soigner un groupe"""
    amount = int(request.form['amount'])
    combat_id = GroupService.apply_group_heal(group_id, amount)

    from app.routes.combat import broadcast_combat_update
    broadcast_combat_update(combat_id)

    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:group_id>/toggle_condition/<condition>')
def toggle_condition_group(group_id, condition):
    """Basculer une condition sur un groupe"""
    combat_id = GroupService.toggle_group_condition(group_id, condition)

    from app.routes.combat import broadcast_combat_update
    broadcast_combat_update(combat_id)

    return redirect(url_for('combat.view_combat', combat_id=combat_id))