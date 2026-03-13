# Migrated to app.web.routes
"""Routes pour la gestion de l'expérience - VERSION SÉCURISÉE"""
from flask import Blueprint, request, redirect, url_for, jsonify, render_template, flash, g
from app.application.use_cases.xp_service import XPService
from app.models import CharacterTemplate
from app.utils.decorators import login_required

# Créer le blueprint
bp = Blueprint('xp', __name__, url_prefix='/xp')


@bp.route('/character/<int:character_id>/award', methods=['POST'])
@login_required
def award_manual_xp(character_id):
    """Attribuer manuellement de l'XP à un personnage"""
    character = CharacterTemplate.query.get_or_404(character_id)

    # ✅ SÉCURITÉ RENFORCÉE avec contexte MJ
    can_award = False
    is_mj_context = False

    # Admin peut tout faire
    if g.current_user.role == 'Admin':
        can_award = True

    # Propriétaire du personnage peut s'attribuer de l'XP
    elif character.owner_id == g.current_user.id:
        can_award = True

    # ✅ NOUVEAU : MJ de la campagne peut donner XP + a accès aux notes privées
    elif character.campaign and g.current_user.is_mj_of(character.campaign):
        can_award = True
        is_mj_context = True

    if not can_award:
        flash('Vous n\'êtes pas autorisé à attribuer de l\'XP à ce personnage.', 'error')
        return redirect(url_for('template.character_profile', id=character_id))

    xp_amount = int(request.form['xp_amount'])
    description = request.form.get('description', 'XP manuelle')

    # ✅ NOUVEAU : Si MJ, peut ajouter contexte dans description
    if is_mj_context:
        mj_context = request.form.get('mj_context', '')
        if mj_context:
            description += f" (MJ: {mj_context})"

    result = XPService.award_xp(
        character_id,
        xp_amount,
        source="manual",
        description=description,
        awarded_by=g.current_user.username
    )

    if result['leveled_up']:
        flash(f'{character.name} est passé niveau {result["new_level"]} !', 'success')

        # ✅ NOUVEAU : Si MJ, suggérer d'ajouter note privée sur la montée de niveau
        if is_mj_context:
            flash(f'💡 Pensez à ajouter une note privée sur cette montée de niveau !', 'info')
    else:
        flash(f'{xp_amount} XP attribués à {character.name}', 'success')

    return redirect(url_for('template.character_profile', id=character_id))


@bp.route('/combat/<int:combat_id>/award_party', methods=['POST'])
@login_required  # ✅ AJOUT : Protection obligatoire
def award_combat_xp(combat_id):
    """Attribuer l'XP de combat à tous les PJ participants"""
    from app.models.combat import Combat

    combat = Combat.query.get_or_404(combat_id)

    # ✅ SÉCURITÉ : Seul le MJ de la campagne ou Admin peut attribuer l'XP de combat
    can_award = False

    if g.current_user.role == 'Admin':
        can_award = True
    elif combat.campaign and g.current_user.is_mj_of(combat.campaign):
        can_award = True

    if not can_award:
        flash('Seul le MJ de la campagne peut attribuer l\'XP de combat.', 'error')
        return redirect(url_for('summary.combat_summary', combat_id=combat_id))

    result = XPService.award_combat_xp_to_party(
        combat_id,
        awarded_by=g.current_user.username  # ✅ AJOUT : Tracer qui donne l'XP
    )

    if 'error' in result:
        flash(result['error'], 'error')
    else:
        flash(f'XP de combat attribuée : {result["xp_awarded"]} XP par personnage', 'success')

    return redirect(url_for('summary.combat_summary', combat_id=combat_id))


@bp.route('/character/<int:character_id>/history')
@login_required  # ✅ AJOUT : Protection obligatoire
def xp_history(character_id):
    """Historique d'XP d'un personnage"""
    character = CharacterTemplate.query.get_or_404(character_id)

    # ✅ SÉCURITÉ : Vérifier que l'utilisateur peut voir ce personnage
    if not character.can_be_viewed_by(g.current_user):
        flash('Vous n\'êtes pas autorisé à voir l\'historique de ce personnage.', 'error')
        return redirect(url_for('main.index'))

    xp_logs = XPService.get_character_xp_history(character_id)

    return render_template(
        'xp_history.html',
        character=character,
        xp_logs=xp_logs
    )