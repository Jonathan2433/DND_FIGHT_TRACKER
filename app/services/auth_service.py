"""Service métier pour l'authentification"""
from datetime import datetime
from flask import url_for
from app.extensions import db
from app.models.user import User, EmailVerification
from app.services.email_service import EmailService


class AuthService:
    """Service principal pour l'authentification"""

    @staticmethod
    def register_user(username, email, password, role='Joueur'):
        """Créer un nouvel utilisateur"""
        # Vérifier unicité
        if User.query.filter_by(username=username).first():
            return {"error": "Ce nom d'utilisateur existe déjà"}

        if User.query.filter_by(email=email).first():
            return {"error": "Cet email est déjà utilisé"}

        # Créer l'utilisateur
        user = User(username=username, email=email, role=role)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # Créer token de vérification
        verification = EmailVerification.create_verification(user.id)

        # Envoyer email
        verification_url = url_for('auth.verify_email',
                                   token=verification.token,
                                   _external=True)

        EmailService.send_verification_email(
            user.email,
            user.username,
            verification_url
        )

        return {
            "success": True,
            "user": user,
            "message": "Compte créé ! Vérifiez votre email pour activer votre compte."
        }

    @staticmethod
    def login_user(username_or_email, password):
        """Connecter un utilisateur"""
        # Chercher par username ou email
        user = User.query.filter(
            (User.username == username_or_email) |
            (User.email == username_or_email)
        ).first()

        if not user or not user.check_password(password):
            return {"error": "Nom d'utilisateur/email ou mot de passe incorrect"}

        if not user.is_verified:
            return {"error": "Compte non vérifié. Vérifiez votre email."}

        if not user.is_active:
            return {"error": "Compte désactivé"}

        # Mettre à jour dernière connexion
        user.last_login = datetime.utcnow()
        db.session.commit()

        return {"success": True, "user": user}

    @staticmethod
    def verify_email(token):
        """Vérifier un token d'email"""
        verification = EmailVerification.query.filter_by(token=token).first()

        if not verification:
            return {"error": "Token invalide"}

        if verification.is_expired:
            return {"error": "Token expiré"}

        if verification.is_used:
            return {"error": "Token déjà utilisé"}

        # Activer l'utilisateur
        user = User.query.get(verification.user_id)
        user.is_verified = True

        verification.is_used = True

        db.session.commit()

        return {"success": True, "user": user}

    @staticmethod
    def get_user_by_id(user_id):
        """Récupérer un utilisateur par ID"""
        return User.query.get(user_id)

    @staticmethod
    def resend_verification(email):
        """Renvoyer un email de vérification"""
        user = User.query.filter_by(email=email).first()

        if not user:
            return {"error": "Email non trouvé"}

        if user.is_verified:
            return {"error": "Compte déjà vérifié"}

        # Créer nouveau token
        verification = EmailVerification.create_verification(user.id)

        verification_url = url_for('auth.verify_email',
                                   token=verification.token,
                                   _external=True)

        EmailService.send_verification_email(
            user.email,
            user.username,
            verification_url
        )

        return {"success": True, "message": "Email de vérification renvoyé"}