"""Service metier pour l'envoi des resumes d'episode par email."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from flask import current_app
from flask_mail import Message

from app.application.use_cases.email_service import EmailService
from app.extensions import db
from app.models.campaign import Campaign, CampaignMember
from app.models.episode import Episode
from app.models.user import User


class EpisodeEmailServiceError(RuntimeError):
    """Erreur de base pour les emails de resume d'episode."""


class EpisodeEmailService:
    """Operations d'envoi d'email pour les resumes d'episode."""

    @staticmethod
    def get_summary_recipients(campaign: Campaign) -> list[dict[str, Any]]:
        """Retourner les destinataires uniques (joueurs + MJ) avec email valide."""
        recipients: dict[str, dict[str, Any]] = {}

        def _push_recipient(user: User | None) -> None:
            if not user or not user.email:
                return
            email = user.email.strip().lower()
            if not email:
                return
            if email not in recipients:
                recipients[email] = {
                    'email': email,
                    'username': user.username,
                }

        _push_recipient(campaign.mj)

        memberships = CampaignMember.query.filter_by(campaign_id=campaign.id).all()
        for membership in memberships:
            _push_recipient(membership.user)

        return list(recipients.values())

    @staticmethod
    def send_episode_summary_email(
        episode: Episode,
        source_hash: str,
        summary_text: str | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        """Envoyer le resume public de l'episode aux participants autorises."""
        summary_to_send = (summary_text or episode.summary_public or '').strip()
        if not summary_to_send:
            episode.summary_email_status = 'failed'
            episode.summary_email_error = 'Resume vide: envoi email annule.'
            db.session.commit()
            raise EpisodeEmailServiceError('Resume vide: envoi email annule.')

        if not force and episode.summary_email_status == 'pending':
            raise EpisodeEmailServiceError('Un envoi email est deja en cours pour cet episode.')

        if not force and episode.summary_last_emailed_hash and episode.summary_last_emailed_hash == source_hash:
            return {
                'sent': False,
                'skipped': True,
                'reason': 'unchanged_summary_already_emailed',
                'recipient_count': 0,
            }

        campaign = episode.story_arc.campaign
        recipients = EpisodeEmailService.get_summary_recipients(campaign)

        if not recipients:
            episode.summary_email_status = 'failed'
            episode.summary_email_error = 'Aucun destinataire email valide pour cette campagne.'
            db.session.commit()
            raise EpisodeEmailServiceError('Aucun destinataire email valide pour cette campagne.')

        # Verrou applicatif simple pour eviter les doubles envois concurrents.
        episode.summary_email_status = 'pending'
        episode.summary_email_error = None
        db.session.commit()

        episode_url = (
            f"{current_app.config.get('BASE_URL', '').rstrip('/')}/episode/{episode.id}"
            if current_app.config.get('BASE_URL') else ''
        )
        campaign_name = campaign.name
        episode_label = episode.title or f'Episode {episode.order_index or episode.id}'

        subject = f"[ExalQuest] Resume de l'episode - {campaign_name}"
        intro = (
            f"Le resume de l'episode \"{episode_label}\" de la campagne "
            f"\"{campaign_name}\" est maintenant disponible."
        )
        summary_html = '<p style="white-space: pre-line; margin: 0;">' + summary_to_send + '</p>'

        html_body = EmailService._build_email_shell(
            title='Resume de l\'episode',
            intro=intro,
            cta_label='Voir l\'episode',
            cta_url=episode_url or '#',
            body_content=(
                f"<p style='margin-top:0;'><strong>Campagne :</strong> {campaign_name}</p>"
                f"<p><strong>Episode :</strong> {episode_label}</p>"
                f"{summary_html}"
            ),
            footer_content='Email envoye automatiquement apres generation du resume d\'episode.',
        )

        text_body = (
            'ExalQuest - Resume d\'episode\n\n'
            f'Campagne : {campaign_name}\n'
            f'Episode : {episode_label}\n\n'
            f'{summary_to_send}\n\n'
            f'Lien : {episode_url if episode_url else "(non configure)"}\n'
        )

        recipient_emails = [entry['email'] for entry in recipients]
        msg = Message(
            subject=subject,
            recipients=recipient_emails,
            html=html_body,
            body=text_body,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
        )

        try:
            send_result = EmailService._send_message(msg, 'email resume episode')
            if send_result.get('error'):
                episode.summary_email_status = 'failed'
                episode.summary_email_error = send_result['error']
                db.session.commit()
                raise EpisodeEmailServiceError(send_result['error'])

            episode.summary_email_status = 'sent'
            episode.summary_email_error = None
            episode.summary_last_emailed_at = datetime.utcnow()
            episode.summary_last_emailed_hash = source_hash
            db.session.commit()

            return {
                'sent': True,
                'skipped': False,
                'recipient_count': len(recipient_emails),
                'recipients': recipient_emails,
            }

        except EpisodeEmailServiceError:
            raise
        except Exception as exc:  # noqa: BLE001 - persistance de statut en echec inattendu
            episode.summary_email_status = 'failed'
            episode.summary_email_error = str(exc)
            db.session.commit()
            raise EpisodeEmailServiceError(str(exc)) from exc
