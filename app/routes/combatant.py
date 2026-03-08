"""Routes pour la gestion des combattants individuels"""
from flask import Blueprint, request, redirect, url_for
from app.services import CombatantService
from app.routes.combat import broadcast_combat_update

# Créer le blueprint
bp = Blueprint('combatant', __name__, url_prefix='/combatant')


@bp.route('/<int:id>/delete', methods=['POST'])
def delete_combatant(id):
    """Supprimer un combattant"""
    combat_id = CombatantService.delete_combatant(id)
    broadcast_combat_update(combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combat_id))


@bp.route('/<int:id>/toggle_visibility')
def toggle_visibility(id):
    """Basculer la visibilité d'un combattant"""
    combatant = CombatantService.toggle_visibility(id)
    broadcast_combat_update(combatant.combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combatant.combat_id))


@bp.route('/<int:id>/toggle_fled')
def toggle_fled(id):
    """Basculer l'état de fuite d'un combattant"""
    combatant = CombatantService.toggle_fled_status(id)
    broadcast_combat_update(combatant.combat_id)
    return redirect(url_for('combat.view_combat', combat_id=combatant.combat_id))


@bp.route('/<int:id>/damage', methods=['POST'])
def damage(id):
    """Infliger des dégâts à un combattant"""
    amount = int(request.form['amount'])
    combatant = CombatantService.apply_damage(id, amount)
    broadcast_combat_update(combatant.combat.id)
    return redirect(url_for('combat.view_combat', combat_id=combatant.combat.id))


@bp.route('/<int:id>/heal', methods=['POST'])
def heal(id):
    """Soigner un combattant"""
    amount = int(request.form['amount'])
    combatant = CombatantService.apply_heal(id, amount)
    broadcast_combat_update(combatant.combat.id)
    return redirect(url_for('combat.view_combat', combat_id=combatant.combat_id))


@bp.route('/<int:id>/modify_ac', methods=['POST'])
def modify_ac(id):
    """Modifier la CA d'un combattant"""
    amount = int(request.form['amount'])
    combatant = CombatantService.modify_ac(id, amount)
    broadcast_combat_update(combatant.combat.id)
    return redirect(url_for('combat.view_combat', combat_id=combatant.combat.id))


@bp.route('/<int:id>/modify_temp_hp', methods=['POST'])
def modify_temp_hp(id):
    """Modifier les PV temporaires d'un combattant"""
    amount = int(request.form['amount'])
    combatant = CombatantService.modify_temp_hp(id, amount)
    broadcast_combat_update(combatant.combat.id)
    return redirect(url_for('combat.view_combat', combat_id=combatant.combat.id))


@bp.route('/<int:id>/toggle_condition/<condition>')
def toggle_condition(id, condition):
    """Basculer une condition sur un combattant"""
    combatant = CombatantService.toggle_condition(id, condition)
    broadcast_combat_update(combatant.combat.id)
    return redirect(url_for('combat.view_combat', combat_id=combatant.combat.id))