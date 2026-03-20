"""Routes du centre de notifications."""
from flask import Blueprint, render_template, redirect, url_for, g, flash, jsonify

from app.application.use_cases.campaign_service import CampaignService
from app.application.use_cases.notification_service import NotificationService
from app.models import Combat
from app.utils.decorators import login_required


bp = Blueprint('notification', __name__, url_prefix='/notifications')


CAMPAIGN_NOTIFICATION_KINDS = {
    'campaign_invitation',
    'campaign_invitation_accepted',
    'campaign_invitation_declined',
    'join_request',
    'join_request_approved',
    'join_request_rejected',
    'campaign_member_left',
    'campaign_member_removed',
    'campaign_closed',
    'shared_npc_added',
    'shared_npc_updated',
    'shared_npc_deleted',
    'shared_pj_added',
    'player_pj_added',
    'player_pj_updated',
    'player_pj_deleted',
    'story_arc_created',
    'campaign_session_created',
    'campaign_session_updated',
    'campaign_session_cancelled',
    'xp_awarded',
}


def _campaign_invitation_action_urls(user_id, notification):
    if notification.kind != 'campaign_invitation' or not notification.campaign_id:
        return None

    invitation = CampaignService.get_pending_invitation_for_user(notification.campaign_id, user_id)
    if not invitation:
        return None

    return {
        'accept_url': url_for('campaign.accept_invitation', token=invitation.token),
        'decline_url': url_for('campaign.decline_invitation', token=invitation.token),
    }


def _notification_target(user_id, notification):
    if notification.kind == 'campaign_invitation' and notification.campaign_id:
        return url_for('campaign.review_invitation', campaign_id=notification.campaign_id)

    if notification.campaign_id and notification.kind in CAMPAIGN_NOTIFICATION_KINDS:
        return url_for('campaign.view_campaign', campaign_id=notification.campaign_id)

    if notification.kind.startswith('combat_invitation:'):
        combat_id = notification.kind.split(':', 1)[1]
        if combat_id.isdigit():
            combat = Combat.query.get(int(combat_id))
            if combat and combat.is_closed:
                return url_for('summary.combat_summary', combat_id=combat.id)
            return url_for('combat.view_combat_player', combat_id=int(combat_id))

    if notification.kind.startswith('player_'):
        return url_for('template.manage_templates')

    return url_for('main.index')


@bp.route('/')
@login_required
def index():
    notifications = NotificationService.list_user_notifications(g.current_user.id, limit=100)
    return render_template('notifications/index.html', notifications=notifications)


@bp.route('/<int:notification_id>/open', methods=['POST'])
@login_required
def open_notification(notification_id):
    notification = NotificationService.mark_as_read(g.current_user.id, notification_id)

    if not notification:
        flash('Notification introuvable.', 'error')
        return redirect(url_for('notification.index'))

    return redirect(_notification_target(g.current_user.id, notification))


@bp.route('/header_data', methods=['GET'])
@login_required
def header_data():
    notifications = NotificationService.list_user_notifications(g.current_user.id, limit=6)

    payload = []
    for notification in notifications:
        actions = _campaign_invitation_action_urls(g.current_user.id, notification)
        payload.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'is_read': notification.is_read,
            'created_at': notification.created_at.strftime('%d/%m/%Y %H:%M'),
            'open_url': url_for('notification.open_notification', notification_id=notification.id),
            'accept_url': actions['accept_url'] if actions else None,
            'decline_url': actions['decline_url'] if actions else None,
        })

    return jsonify({
        'unread_count': NotificationService.unread_count(g.current_user.id),
        'notifications': payload,
    })


@bp.route('/mark_all_read', methods=['POST'])
@login_required
def mark_all_read():
    NotificationService.mark_all_as_read(g.current_user.id)
    return redirect(url_for('notification.index'))


@bp.route('/clear_all', methods=['POST'])
@login_required
def clear_all():
    NotificationService.clear_all(g.current_user.id)
    flash('Toutes les notifications ont été supprimées.', 'success')
    return redirect(url_for('notification.index'))
