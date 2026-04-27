# Migrated to app.web.routes
"""Routes pour la gestion de l'experience."""
from flask import Blueprint, request, redirect, url_for, render_template, flash, g

from app.application.use_cases.xp_service import XPService
from app.application.use_cases.notification_service import NotificationService
from app.models import CharacterTemplate
from app.utils.decorators import login_required


bp = Blueprint('xp', __name__, url_prefix='/xp')


@bp.route('/character/<int:character_id>/award', methods=['POST'])
@login_required
def award_manual_xp(character_id):
    """Attribuer manuellement de l'XP a un personnage."""
    character = CharacterTemplate.query.get_or_404(character_id)

    is_main_campaign_mj = bool(character.campaign and g.current_user.is_mj_of(character.campaign))
    is_linked_campaign_mj = any(g.current_user.is_mj_of(campaign) for campaign in character.campaigns)
    can_award = is_main_campaign_mj or is_linked_campaign_mj
    is_mj_context = can_award

    if not can_award:
        flash("Seul le MJ de la campagne peut attribuer de l'XP a ce personnage.", 'error')
        return redirect(url_for('template.character_profile', id=character_id))

    xp_amount = int(request.form['xp_amount'])
    description = request.form.get('description', 'XP manuelle')

    if is_mj_context:
        mj_context = request.form.get('mj_context', '').strip()
        if mj_context:
            description += f" (MJ: {mj_context})"

    result = XPService.award_xp(
        character_id,
        xp_amount,
        source="manual",
        description=description,
        awarded_by=g.current_user.username,
    )

    if is_mj_context and character.owner_id != g.current_user.id:
        NotificationService.create_notification(
            character.owner_id,
            "XP accordée",
            f'Le MJ a accordé {xp_amount} XP à votre PJ "{character.name}".',
            kind='xp_awarded',
            campaign_id=character.campaign_id,
        )

    if result['leveled_up']:
        flash(f"{character.name} est passe niveau {result['new_level']} !", 'success')
        if is_mj_context:
            flash("Pensez a noter cette montee de niveau dans le suivi de campagne.", 'info')
    else:
        flash(f"{xp_amount} XP attribues a {character.name}", 'success')

    return redirect(url_for('template.character_profile', id=character_id))


@bp.route('/combat/<int:combat_id>/award_party', methods=['POST'])
@login_required
def award_combat_xp(combat_id):
    """Attribuer l'XP de combat a tous les PJ participants."""
    from app.models.combat import Combat

    combat = Combat.query.get_or_404(combat_id)

    can_award = False
    if g.current_user.role == 'Admin':
        can_award = True
    elif combat.campaign and g.current_user.is_mj_of(combat.campaign):
        can_award = True

    if not can_award:
        flash("Seul le MJ de la campagne peut attribuer l'XP de combat.", 'error')
        return redirect(url_for('summary.combat_summary', combat_id=combat_id))

    result = XPService.award_combat_xp_to_party(
        combat_id,
        awarded_by=g.current_user.username,
    )

    if 'error' in result:
        flash(result['error'], 'error')
    else:
        flash(f"XP de combat attribuee : {result['xp_awarded']} XP par personnage", 'success')

    return redirect(url_for('summary.combat_summary', combat_id=combat_id))


@bp.route('/character/<int:character_id>/history')
@login_required
def xp_history(character_id):
    """Historique d'XP d'un personnage."""
    character = CharacterTemplate.query.get_or_404(character_id)

    if not character.can_be_viewed_by(g.current_user):
        flash("Vous n'etes pas autorise a voir l'historique de ce personnage.", 'error')
        return redirect(url_for('main.index'))

    is_campaign_mj = bool(
        (character.campaign and g.current_user.is_mj_of(character.campaign))
        or any(g.current_user.is_mj_of(campaign) for campaign in character.campaigns)
    )
    can_view_xp = is_campaign_mj

    if not can_view_xp:
        flash("Seul le MJ de la campagne peut consulter l'historique XP de ce personnage.", 'error')
        return redirect(url_for('template.character_profile', id=character_id))

    xp_logs = XPService.get_character_xp_history(character_id)

    return render_template(
        'xp_history.html',
        character=character,
        xp_logs=xp_logs,
    )
