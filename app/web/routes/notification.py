"""Routes du centre de notifications."""
from flask import Blueprint, render_template, redirect, url_for, g

from app.application.use_cases.notification_service import NotificationService
from app.utils.decorators import login_required


bp = Blueprint('notification', __name__, url_prefix='/notifications')


@bp.route('/')
@login_required
def index():
    notifications = NotificationService.list_user_notifications(g.current_user.id, limit=100)
    return render_template('notifications/index.html', notifications=notifications)


@bp.route('/mark_all_read', methods=['POST'])
@login_required
def mark_all_read():
    NotificationService.mark_all_as_read(g.current_user.id)
    return redirect(url_for('notification.index'))
