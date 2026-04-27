"""Service métier pour la gestion des notifications."""

from app.extensions import db
from app.extensions import socketio
from app.models.notification import Notification
from app.models.campaign import CampaignMember


class NotificationService:
    """Opérations de création et lecture des notifications."""

    @staticmethod
    def _emit_realtime_update(user_id):
        unread_count = NotificationService.unread_count(user_id)
        socketio.emit(
            'notification_update',
            {'unread_count': unread_count},
            room=f'user_{user_id}',
        )

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
            NotificationService._emit_realtime_update(user_id)
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
            for user_id in recipients:
                NotificationService._emit_realtime_update(user_id)

    @staticmethod
    def list_user_notifications(user_id, limit=25):
        return Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_user_notification(user_id, notification_id):
        return Notification.query.filter_by(id=notification_id, user_id=user_id).first()

    @staticmethod
    def unread_count(user_id):
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    @staticmethod
    def mark_all_as_read(user_id):
        Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()
        NotificationService._emit_realtime_update(user_id)

    @staticmethod
    def clear_all(user_id):
        Notification.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        NotificationService._emit_realtime_update(user_id)

    @staticmethod
    def mark_as_read(user_id, notification_id):
        notification = NotificationService.get_user_notification(user_id, notification_id)
        if not notification:
            return None

        if not notification.is_read:
            notification.is_read = True
            db.session.commit()
            NotificationService._emit_realtime_update(user_id)

        return notification
