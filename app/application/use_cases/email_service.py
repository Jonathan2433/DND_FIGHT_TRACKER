# Migrated to application layer
"""Service pour l'envoi d'emails"""
from flask import current_app
from flask_mail import Message

from app.extensions import mail


class EmailService:
    """Service pour l'envoi d'emails"""

    @staticmethod
    def _validate_email_configuration():
        """Valider que la configuration SMTP minimale est bien présente."""
        missing = []
        if not current_app.config.get("MAIL_USERNAME"):
            missing.append("MAIL_USERNAME")
        if not current_app.config.get("MAIL_PASSWORD"):
            missing.append("MAIL_PASSWORD")
        if not current_app.config.get("MAIL_DEFAULT_SENDER"):
            missing.append("MAIL_DEFAULT_SENDER")

        if missing:
            return {
                "error": (
                    "Configuration email incomplète. Variables manquantes: "
                    + ", ".join(missing)
                )
            }

        return None

    @staticmethod
    def _send_message(msg, log_context="email"):
        """Envoyer un message avec logs homogènes."""
        config_error = EmailService._validate_email_configuration()
        if config_error:
            current_app.logger.error(config_error["error"])
            return config_error

        try:
            mail.send(msg)
            return {"success": True}
        except Exception as e:
            current_app.logger.error(f"Erreur envoi {log_context}: {e}")
            return {"error": f"Erreur lors de l'envoi: {e}"}

    @staticmethod
    def _build_email_shell(title, intro, cta_label, cta_url, body_content, footer_content):
        """Construire un template email aligné sur la DA ExalQuest."""
        app_name = "ExalQuest"
        return f"""
        <html>
        <body style="margin: 0; padding: 0; background-color: #0b0d1d; font-family: 'Poppins', 'Segoe UI', Arial, sans-serif; color: #f4f4ff;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background: radial-gradient(circle at 0% 0%, rgba(88, 83, 255, 0.2), transparent 45%), radial-gradient(circle at 100% 0%, rgba(254, 44, 155, 0.18), transparent 40%), linear-gradient(180deg, #0f1127 0%, #0b0d1d 100%); padding: 24px 12px;">
                <tr>
                    <td align="center">
                        <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width: 640px; background: #1d2250; border: 1px solid #3f468f; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 24px rgba(8, 10, 26, 0.5);">
                            <tr>
                                <td style="padding: 28px 28px 20px 28px; border-bottom: 1px solid #32396f;">
                                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                                        <tr>
                                            <td>
                                                <div style="display: inline-block; background: #fe2c9b; color: #ffffff; padding: 6px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; letter-spacing: 0.04em;">EQ</div>
                                                <h1 style="margin: 12px 0 4px 0; font-size: 26px; line-height: 1.2; color: #ffffff;">{app_name}</h1>
                                                <p style="margin: 0; color: #d5d5eb; font-size: 14px;">Suivi de campagnes et combats pour JDR</p>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 28px;">
                                    <h2 style="margin: 0 0 14px 0; font-size: 24px; color: #ffffff;">{title}</h2>
                                    <p style="margin: 0 0 18px 0; color: #deddff; font-size: 15px; line-height: 1.6;">{intro}</p>
                                    <div style="margin-bottom: 22px; color: #f4f4ff; font-size: 15px; line-height: 1.7;">{body_content}</div>

                                    <table role="presentation" cellpadding="0" cellspacing="0" style="margin: 28px 0 22px 0;">
                                        <tr>
                                            <td align="center" style="border-radius: 10px; background: linear-gradient(135deg, #fe2c9b 0%, #5853ff 100%);">
                                                <a href="{cta_url}" style="display: inline-block; padding: 14px 28px; font-size: 15px; font-weight: 700; color: #ffffff; text-decoration: none; border-radius: 10px;">{cta_label}</a>
                                            </td>
                                        </tr>
                                    </table>

                                    <p style="margin: 0 0 8px 0; color: #b9bbe4; font-size: 13px; line-height: 1.5;">
                                        Si le bouton ne fonctionne pas, copiez-collez ce lien dans votre navigateur :
                                    </p>
                                    <p style="margin: 0; word-break: break-all;">
                                        <a href="{cta_url}" style="color: #ffda3e; font-size: 13px;">{cta_url}</a>
                                    </p>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 18px 28px 24px 28px; border-top: 1px solid #32396f; background: #161a3a;">
                                    <p style="margin: 0; color: #9797cd; font-size: 12px; line-height: 1.6;">{footer_content}</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

    @staticmethod
    def send_verification_email(user_email, username, verification_url):
        """Envoyer un email de vérification"""
        subject = "🎲 Vérification de votre compte DND Combat Tracker"

        html_body = EmailService._build_email_shell(
            title=f"Bienvenue, {username} !",
            intro="Merci d'avoir créé votre compte sur ExalQuest.",
            cta_label="✅ Vérifier mon compte",
            cta_url=verification_url,
            body_content=(
                "Pour activer votre compte et accéder à vos campagnes, "
                "merci de confirmer votre adresse email en cliquant sur le bouton ci-dessous."
            ),
            footer_content=(
                "Ce lien expire dans 24 heures. Si vous n'êtes pas à l'origine de cette inscription, "
                "vous pouvez ignorer cet email."
            ),
        )

        text_body = f"""
        ExalQuest - Vérification de compte

        Bienvenue, {username} !

        Pour activer votre compte, cliquez sur ce lien :
        {verification_url}

        Ce lien expire dans 24 heures.
        """

        msg = Message(
            subject=subject,
            recipients=[user_email],
            html=html_body,
            body=text_body,
            sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
        )

        return EmailService._send_message(msg, "email de vérification")

    @staticmethod
    def send_password_reset_email(user_email, username, reset_url):
        """Envoyer un email de reset de mot de passe (pour plus tard)"""
        # Implémentation pour plus tard
        pass

    @staticmethod
    def send_campaign_invitation(user_email, campaign_name, invitation_url, username):
        """Envoyer un email d'invitation à une campagne"""
        subject = f"🎲 Invitation à rejoindre la campagne : {campaign_name}"

        html_body = EmailService._build_email_shell(
            title="Vous êtes invité(e) !",
            intro=f"Salut {username}, une place vous attend dans l'aventure.",
            cta_label="🎯 Rejoindre la campagne",
            cta_url=invitation_url,
            body_content=(
                "Vous avez été invité(e) à rejoindre la campagne "
                f"<strong style='color: #ffda3e;'>&laquo;&nbsp;{campaign_name}&nbsp;&raquo;</strong> sur ExalQuest."
            ),
            footer_content=(
                "Cette invitation expire dans 7 jours. Si vous n'êtes pas concerné(e), "
                "vous pouvez ignorer cet email."
            ),
        )

        text_body = f"""
        ExalQuest - Invitation à rejoindre une campagne

        Vous avez été invité(e) à rejoindre la campagne "{campaign_name}" !

        Cliquez sur ce lien pour rejoindre :
        {invitation_url}

        Cette invitation expire dans 7 jours.
        """

        msg = Message(
            subject=subject,
            recipients=[user_email],
            html=html_body,
            body=text_body,
            sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
        )

        return EmailService._send_message(msg, "email campagne")

    @staticmethod
    def send_campaign_signup_invitation(user_email, campaign_name, signup_url):
        """Envoyer un email d'invitation pour creer un compte puis rejoindre une campagne."""
        subject = f"🎲 Invitation à rejoindre la campagne : {campaign_name}"

        html_body = EmailService._build_email_shell(
            title="Vous êtes invité(e) à l'aventure !",
            intro="Un MJ vous invite à créer votre compte pour rejoindre sa campagne.",
            cta_label="🛡️ Créer mon compte",
            cta_url=signup_url,
            body_content=(
                "Vous avez été invité(e) à rejoindre la campagne "
                f"<strong style='color: #ffda3e;'>&laquo;&nbsp;{campaign_name}&nbsp;&raquo;</strong> sur ExalQuest.<br><br>"
                "Créez votre compte avec cette adresse email, puis l'invitation sera utilisable pour rejoindre automatiquement la campagne."
            ),
            footer_content=(
                "Cette invitation expire dans 7 jours. Si vous n'êtes pas concerné(e), "
                "vous pouvez ignorer cet email."
            ),
        )

        text_body = f"""
        ExalQuest - Invitation a rejoindre une campagne

        Vous avez ete invite(e) a rejoindre la campagne "{campaign_name}".

        Creez votre compte puis rejoignez la campagne via ce lien :
        {signup_url}

        Cette invitation expire dans 7 jours.
        """

        msg = Message(
            subject=subject,
            recipients=[user_email],
            html=html_body,
            body=text_body,
            sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
        )

        return EmailService._send_message(msg, "email invitation inscription campagne")

    @staticmethod
    def send_combat_invitation(user_email, username, campaign_name, combat_name, invitation_url):
        """Envoyer un email d'invitation directe vers la vue joueur d'un combat."""
        subject = f"⚔️ Invitation au combat : {combat_name}"

        html_body = EmailService._build_email_shell(
            title="Le combat commence !",
            intro=f"Salut {username}, le MJ te convie immédiatement à la bataille.",
            cta_label="⚔️ Rejoindre le combat",
            cta_url=invitation_url,
            body_content=(
                "Tu es invité(e) à rejoindre le combat "
                f"<strong style='color: #ffda3e;'>&laquo;&nbsp;{combat_name}&nbsp;&raquo;</strong> "
                f"de la campagne <strong>{campaign_name}</strong>."
            ),
            footer_content=(
                "Clique sur le bouton pour arriver directement sur la vue joueur du combat. "
                "Si tu n'es pas concerné(e), ignore simplement cet email."
            ),
        )

        text_body = f"""
        ExalQuest - Invitation au combat

        Salut {username},

        Tu es invité(e) au combat "{combat_name}" (campagne "{campaign_name}").

        Rejoins directement la vue joueur ici :
        {invitation_url}
        """

        msg = Message(
            subject=subject,
            recipients=[user_email],
            html=html_body,
            body=text_body,
            sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
        )

        return EmailService._send_message(msg, "email invitation combat")

    @staticmethod
    def send_campaign_session_reminder(user_email, username, campaign_name, scheduled_for):
        """Envoyer un email de rappel de session de campagne à J-7."""
        session_label = scheduled_for.strftime('%d/%m/%Y à %Hh%M')
        campaign_url = f"{current_app.config.get('BASE_URL', '').rstrip('/')}/campaign/"
        subject = f"🗓️ Rappel session dans 7 jours : {campaign_name}"

        html_body = EmailService._build_email_shell(
            title="Rappel de session",
            intro=f"Salut {username}, votre prochaine aventure approche.",
            cta_label="🎲 Voir la campagne",
            cta_url=campaign_url,
            body_content=(
                "La prochaine session de la campagne "
                f"<strong style='color: #ffda3e;'>&laquo;&nbsp;{campaign_name}&nbsp;&raquo;</strong> "
                f"est prévue le <strong>{session_label}</strong>."
            ),
            footer_content=(
                "Ce rappel automatique est envoyé 7 jours avant la date de session. "
                "Si la session est modifiée ou annulée, la date affichée peut évoluer."
            ),
        )

        text_body = f"""
        ExalQuest - Rappel de session

        Salut {username},

        La prochaine session de la campagne "{campaign_name}" est prévue le {session_label}.

        Retrouve la campagne ici :
        {campaign_url}
        """

        msg = Message(
            subject=subject,
            recipients=[user_email],
            html=html_body,
            body=text_body,
            sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
        )

        return EmailService._send_message(msg, "email rappel session campagne")
