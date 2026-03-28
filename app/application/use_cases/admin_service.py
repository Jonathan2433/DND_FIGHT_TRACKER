"""Use cases d'administration et de supervision."""
from datetime import datetime, timedelta

from flask import g
from sqlalchemy import func

from app.extensions import db
from app.models import Campaign, CampaignMember, User
from app.models.activity import SiteActivityLog


class AdminService:
    """Service dédié au back office administrateur."""

    @staticmethod
    def log_request_activity(request, response, started_at):
        """Tracer une requête HTTP pour audit technique."""
        if request.endpoint == 'static' or request.path.startswith('/static/'):
            return

        duration_ms = None
        if started_at:
            duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)

        current_user = getattr(g, 'current_user', None)

        log_entry = SiteActivityLog(
            user_id=current_user.id if current_user else None,
            path=request.path[:255],
            method=request.method,
            endpoint=(request.endpoint or '')[:120] or None,
            status_code=response.status_code,
            ip_address=(request.headers.get('X-Forwarded-For', request.remote_addr) or '')[:45] or None,
            user_agent=(request.user_agent.string or '')[:255] or None,
            duration_ms=duration_ms,
        )
        db.session.add(log_entry)
        db.session.commit()

    @staticmethod
    def get_dashboard_metrics(days=30):
        """Récupérer les KPI principaux du back office."""
        since = datetime.utcnow() - timedelta(days=days)

        active_users = (
            db.session.query(func.count(func.distinct(SiteActivityLog.user_id)))
            .filter(SiteActivityLog.created_at >= since)
            .scalar()
        ) or 0

        total_requests = (
            db.session.query(func.count(SiteActivityLog.id))
            .filter(SiteActivityLog.created_at >= since)
            .scalar()
        ) or 0

        new_users = User.query.filter(User.created_at >= since).count()

        total_campaigns = Campaign.query.count()
        active_campaigns = Campaign.query.filter(Campaign.is_active.is_(True)).count()

        campaigns_by_mj = (
            db.session.query(User.username, func.count(Campaign.id).label('campaign_count'))
            .join(Campaign, Campaign.mj_id == User.id)
            .group_by(User.id)
            .order_by(func.count(Campaign.id).desc())
            .limit(10)
            .all()
        )

        recent_activity = (
            SiteActivityLog.query
            .order_by(SiteActivityLog.created_at.desc())
            .limit(100)
            .all()
        )

        recent_signups = (
            User.query
            .order_by(User.created_at.desc())
            .limit(20)
            .all()
        )

        return {
            'since': since,
            'active_users': active_users,
            'total_requests': total_requests,
            'new_users': new_users,
            'total_campaigns': total_campaigns,
            'active_campaigns': active_campaigns,
            'campaigns_by_mj': campaigns_by_mj,
            'recent_activity': recent_activity,
            'recent_signups': recent_signups,
        }

    @staticmethod
    def list_users(limit=200):
        """Lister les utilisateurs avec informations de modération."""
        return User.query.order_by(User.created_at.desc()).limit(limit).all()

    @staticmethod
    def deactivate_user(admin_user_id, target_user_id):
        """Désactiver un compte utilisateur."""
        target = User.query.get_or_404(target_user_id)

        if target.id == admin_user_id:
            return {'error': 'Vous ne pouvez pas désactiver votre propre compte.'}

        target.is_active = False
        db.session.commit()
        return {'success': True, 'user': target}

    @staticmethod
    def reactivate_user(target_user_id):
        """Réactiver un compte utilisateur."""
        target = User.query.get_or_404(target_user_id)
        target.is_active = True
        db.session.commit()
        return {'success': True, 'user': target}

    @staticmethod
    def campaign_membership_count(user_id):
        """Nombre de campagnes où un utilisateur est membre."""
        return CampaignMember.query.filter_by(user_id=user_id).count()
