"""Service d'envoi des emails de rappel de sessions de campagne."""
from datetime import datetime, time, timedelta

from app.extensions import db
from app.models.campaign import Campaign, CampaignSession
from app.application.use_cases.email_service import EmailService


class CampaignSessionReminderService:
    """Orchestration des rappels email de sessions à J-7."""

    @staticmethod
    def send_weekly_session_reminders(reference_time=None):
        """Envoyer les rappels pour les sessions prévues exactement dans 7 jours.

        Le traitement est idempotent grâce à ``CampaignSession.reminder_sent_at``.
        """
        now = reference_time or datetime.utcnow()

        target_date = (now + timedelta(days=7)).date()
        window_start = datetime.combine(target_date, time.min)
        window_end = window_start + timedelta(days=1)

        sessions = (
            CampaignSession.query
            .join(Campaign, Campaign.id == CampaignSession.campaign_id)
            .filter(Campaign.is_active.is_(True))
            .filter(CampaignSession.is_cancelled.is_(False))
            .filter(CampaignSession.reminder_sent_at.is_(None))
            .filter(CampaignSession.scheduled_for >= window_start)
            .filter(CampaignSession.scheduled_for < window_end)
            .all()
        )

        sent_sessions = 0
        failed_sessions = 0

        for campaign_session in sessions:
            campaign = campaign_session.campaign
            recipients_by_email = {}

            mj = campaign.mj
            if mj and mj.email and mj.is_active:
                recipients_by_email[mj.email.lower()] = mj

            for membership in campaign.members:
                user = membership.user
                if not user or not user.email or not user.is_active:
                    continue
                recipients_by_email[user.email.lower()] = user

            session_success = True
            for user in recipients_by_email.values():
                result = EmailService.send_campaign_session_reminder(
                    user_email=user.email,
                    username=user.username,
                    campaign_name=campaign.name,
                    scheduled_for=campaign_session.scheduled_for,
                )

                if result.get('error'):
                    session_success = False

            if session_success:
                campaign_session.reminder_sent_at = datetime.utcnow()
                sent_sessions += 1
            else:
                failed_sessions += 1

        if sessions:
            db.session.commit()

        return {
            'target_date': target_date.isoformat(),
            'sessions_found': len(sessions),
            'sessions_sent': sent_sessions,
            'sessions_failed': failed_sessions,
        }
