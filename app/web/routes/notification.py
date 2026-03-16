"""Routes du centre de notifications."""
from flask import Blueprint, render_template, redirect, url_for, g, flash

from app.application.use_cases.notification_service import NotificationService
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
    'xp_awarded',
}


def _notification_target(notification):
    if notification.campaign_id and notification.kind in CAMPAIGN_NOTIFICATION_KINDS:
        return url_for('campaign.view_campaign', campaign_id=notification.campaign_id)

    if notification.kind.startswith('combat_invitation:'):
        combat_id = notification.kind.split(':', 1)[1]
        if combat_id.isdigit():
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

    return redirect(_notification_target(notification))


@bp.route('/mark_all_read', methods=['POST'])
@login_required
def mark_all_read():
    NotificationService.mark_all_as_read(g.current_user.id)
    return redirect(url_for('notification.index'))
