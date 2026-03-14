"""Service métier pour la gestion des notifications."""

from app.extensions import db
from app.models.notification import Notification
from app.models.campaign import CampaignMember


class NotificationService:
    """Opérations de création et lecture des notifications."""

    @staticmethod
    def create_notification(user_id, title, message, *, kind='general', campaign_id=None, auto_commit=True):
        notification = Notification(
            user_id=user_id,
            campaign_id=campaign_id,
            title=title,
            message=message,
            kind=kind,
        )
        db.session.add(notification)
        if auto_commit:
            db.session.commit()
        return notification

    @staticmethod
    def create_campaign_notification(campaign, title, message, *, kind='campaign', include_mj=False, auto_commit=True):
        recipients = {member.user_id for member in CampaignMember.query.filter_by(campaign_id=campaign.id).all()}
        if include_mj:
            recipients.add(campaign.mj_id)

        for user_id in recipients:
            db.session.add(Notification(
                user_id=user_id,
                campaign_id=campaign.id,
                title=title,
                message=message,
                kind=kind,
            ))

        if auto_commit:
            db.session.commit()

    @staticmethod
    def list_user_notifications(user_id, limit=25):
        return Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(limit).all()

    @staticmethod
    def unread_count(user_id):
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    @staticmethod
    def mark_all_as_read(user_id):
        Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()
