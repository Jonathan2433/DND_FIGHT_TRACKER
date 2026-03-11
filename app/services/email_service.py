"""Service pour l'envoi d'emails"""
from flask import current_app
from flask_mail import Message
from app.extensions import mail


class EmailService:
    """Service pour l'envoi d'emails"""

    @staticmethod
    def send_verification_email(user_email, username, verification_url):
        """Envoyer un email de vérification"""
        subject = "🎲 Vérification de votre compte DND Combat Tracker"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #1e1f26; color: #f0f0f0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #2a2c36; padding: 30px; border-radius: 12px; border: 2px solid #4caf50;">
                <h1 style="color: #4caf50; text-align: center;">🎲 DND Combat Tracker</h1>
                
                <h2 style="color: #f0f0f0;">Bienvenue, {username} !</h2>
                
                <p>Merci de vous être inscrit sur DND Combat Tracker !</p>
                
                <p>Pour activer votre compte et commencer à gérer vos campagnes, veuillez cliquer sur le lien ci-dessous :</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background-color: #4caf50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                        ✅ Vérifier mon compte
                    </a>
                </div>
                
                <p style="color: #ccc; font-size: 14px;">
                    Si le bouton ne fonctionne pas, copiez ce lien dans votre navigateur :<br>
                    <a href="{verification_url}" style="color: #4caf50;">{verification_url}</a>
                </p>
                
                <p style="color: #ccc; font-size: 12px; margin-top: 30px;">
                    Ce lien expire dans 24 heures. Si vous n'avez pas demandé cette inscription, ignorez cet email.
                </p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        DND Combat Tracker - Vérification de compte
        
        Bienvenue, {username} !
        
        Pour activer votre compte, cliquez sur ce lien :
        {verification_url}
        
        Ce lien expire dans 24 heures.
        """

        msg = Message(
            subject=subject,
            recipients=[user_email],
            html=html_body,
            body=text_body
        )

        try:
            mail.send(msg)
            return {"success": True}
        except Exception as e:
            current_app.logger.error(f"Erreur envoi email: {e}")
            return {"error": f"Erreur lors de l'envoi: {e}"}

    @staticmethod
    def send_password_reset_email(user_email, username, reset_url):
        """Envoyer un email de reset de mot de passe (pour plus tard)"""
        # Implémentation pour plus tard
        pass

@staticmethod
def send_campaign_invitation(user_email, campaign_name, invitation_url, username):
    """Envoyer un email d'invitation à une campagne"""
    subject = f"🎲 Invitation à rejoindre la campagne : {campaign_name}"

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #1e1f26; color: #f0f0f0; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #2a2c36; padding: 30px; border-radius: 12px; border: 2px solid #4caf50;">
            <h1 style="color: #4caf50; text-align: center;">🎲 DND Combat Tracker</h1>

            <h2 style="color: #f0f0f0;">Vous êtes invité(e) !</h2>

            <p>Salut {username} !</p>

            <p>Vous avez été invité(e) à rejoindre la campagne <strong style="color: #4caf50;">"{campaign_name}"</strong> sur DND Combat Tracker !</p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{invitation_url}" 
                   style="background-color: #4caf50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                    🎯 Rejoindre la Campagne
                </a>
            </div>

            <p style="color: #ccc; font-size: 14px;">
                Si le bouton ne fonctionne pas, copiez ce lien dans votre navigateur :<br>
                <a href="{invitation_url}" style="color: #4caf50;">{invitation_url}</a>
            </p>

            <p style="color: #ccc; font-size: 12px; margin-top: 30px;">
                Cette invitation expire dans 7 jours. Si vous n'avez pas demandé à rejoindre cette campagne, ignorez cet email.
            </p>
        </div>
    </body>
    </html>
    """

    text_body = f"""
    DND Combat Tracker - Invitation à rejoindre une campagne

    Vous avez été invité(e) à rejoindre la campagne "{campaign_name}" !

    Cliquez sur ce lien pour rejoindre :
    {invitation_url}

    Cette invitation expire dans 7 jours.
    """

    msg = Message(
        subject=subject,
        recipients=[user_email],
        html=html_body,
        body=text_body
    )

    try:
        mail.send(msg)
        return {"success": True}
    except Exception as e:
        current_app.logger.error(f"Erreur envoi email campagne: {e}")
        return {"error": f"Erreur lors de l'envoi: {e}"}