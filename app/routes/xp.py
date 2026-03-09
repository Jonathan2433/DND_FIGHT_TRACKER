"""Routes pour la gestion de l'expérience"""
from flask import Blueprint, request, redirect, url_for, jsonify, render_template
from app.services.xp_service import XPService
from app.models import CharacterTemplate

# Créer le blueprint
bp = Blueprint('xp', __name__, url_prefix='/xp')


@bp.route('/character/<int:character_id>/award', methods=['POST'])
def award_manual_xp(character_id):
    """Attribuer manuellement de l'XP à un personnage"""
    xp_amount = int(request.form['xp_amount'])
    description = request.form.get('description', 'XP manuelle')

    result = XPService.award_xp(
        character_id,
        xp_amount,
        source="manual",
        description=description,
        awarded_by=request.form.get('awarded_by', 'DM')
    )

    if result['leveled_up']:
        # Vous pourriez ajouter une notification flash ici
        pass

    return redirect(url_for('template.character_profile', id=character_id))


@bp.route('/combat/<int:combat_id>/award_party', methods=['POST'])
def award_combat_xp(combat_id):
    """Attribuer l'XP de combat à tous les PJ participants"""
    result = XPService.award_combat_xp_to_party(
        combat_id,
        awarded_by=request.form.get('awarded_by', 'DM')
    )

    return redirect(url_for('summary.combat_summary', combat_id=combat_id))


@bp.route('/character/<int:character_id>/history')
def xp_history(character_id):
    """Historique d'XP d'un personnage"""
    character = CharacterTemplate.query.get_or_404(character_id)
    xp_logs = XPService.get_character_xp_history(character_id)

    return render_template(
        'xp_history.html',
        character=character,
        xp_logs=xp_logs
    )