"""Routes du back office administrateur."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app.application.use_cases.admin_service import AdminService
from app.utils.decorators import admin_required


bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/')
@admin_required
def dashboard():
    """Dashboard admin avec suivi d'activité."""
    metrics = AdminService.get_dashboard_metrics(days=30)
    users = AdminService.list_users(limit=200)

    user_stats = {
        user.id: {
            'campaigns_owned': len(user.owned_campaigns),
            'campaigns_joined': AdminService.campaign_membership_count(user.id),
        }
        for user in users
    }

    return render_template(
        'admin/dashboard.html',
        metrics=metrics,
        users=users,
        user_stats=user_stats,
    )


@bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_user(user_id):
    """Désactiver un utilisateur qui dépasse les limites."""
    result = AdminService.deactivate_user(g.current_user.id, user_id)

    if 'error' in result:
        flash(result['error'], 'error')
    else:
        flash(f"Le compte {result['user'].username} a été désactivé.", 'success')

    return redirect(request.referrer or url_for('admin.dashboard'))


@bp.route('/users/<int:user_id>/reactivate', methods=['POST'])
@admin_required
def reactivate_user(user_id):
    """Réactiver un utilisateur."""
    result = AdminService.reactivate_user(user_id)
    flash(f"Le compte {result['user'].username} a été réactivé.", 'success')
    return redirect(request.referrer or url_for('admin.dashboard'))
