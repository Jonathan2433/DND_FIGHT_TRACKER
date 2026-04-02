# Migrated to application layer
"""Service métier pour l'authentification"""
from datetime import datetime, timedelta

from flask import current_app, url_for
from sqlalchemy import func

from app.extensions import db
from app.models.user import User, EmailVerification, PasswordResetToken
from app.application.use_cases.email_service import EmailService


class AuthService:
    """Service principal pour l'authentification"""

    PASSWORD_RESET_TOKEN_LIFETIME_MINUTES = 30
    PASSWORD_RESET_MAX_PER_HOUR = 3
    PASSWORD_RESET_MAX_PER_DAY = 6

    @staticmethod
    def register_user(username, email, password, role='Joueur'):
        """Créer un nouvel utilisateur"""
        # ✅ SÉCURITÉ : Bloquer la création d'admin via inscription
        if role == 'Admin':
            return {"error": "Le rôle Administrateur ne peut pas être créé via inscription"}

        # ✅ SÉCURITÉ : Seuls Joueur, MJ ou combinaison MJ+Joueur autorisés
        if role not in ['Joueur', 'MJ', 'MJ+Joueur']:
            return {"error": "Rôle non autorisé"}

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

    @staticmethod
    def _password_reset_rate_limited(user_id):
        """Limiter les demandes de reset pour éviter l'abus."""
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)

        hour_count = db.session.query(func.count(PasswordResetToken.id)).filter(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.created_at >= one_hour_ago,
        ).scalar() or 0

        day_count = db.session.query(func.count(PasswordResetToken.id)).filter(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.created_at >= one_day_ago,
        ).scalar() or 0

        return (
            hour_count >= AuthService.PASSWORD_RESET_MAX_PER_HOUR
            or day_count >= AuthService.PASSWORD_RESET_MAX_PER_DAY
        )

    @staticmethod
    def request_password_reset(email_or_username, request_ip=None, request_user_agent=None):
        """Initier un reset de mot de passe avec anti-enumération."""
        generic_result = {
            "success": True,
            "message": (
                "Si un compte existe pour cet identifiant, un email de reinitialisation a ete envoye."
            ),
        }

        lookup = (email_or_username or '').strip()
        if not lookup:
            return generic_result

        user = User.query.filter(
            (User.username == lookup) |
            (User.email == lookup)
        ).first()

        if not user or not user.is_active or not user.is_verified:
            return generic_result

        if AuthService._password_reset_rate_limited(user.id):
            current_app.logger.warning(
                "Password reset rate-limited user_id=%s ip=%s",
                user.id,
                request_ip,
            )
            return generic_result

        PasswordResetToken.query.filter_by(user_id=user.id, used_at=None).update(
            {PasswordResetToken.used_at: datetime.utcnow()}
        )

        reset_token, raw_token = PasswordResetToken.create_for_user(
            user_id=user.id,
            requested_ip=request_ip,
            requested_user_agent=request_user_agent,
            lifetime_minutes=AuthService.PASSWORD_RESET_TOKEN_LIFETIME_MINUTES,
        )

        reset_url = url_for('auth.reset_password', token=raw_token, _external=True)
        EmailService.send_password_reset_email(
            user_email=user.email,
            username=user.username,
            reset_url=reset_url,
            expires_minutes=AuthService.PASSWORD_RESET_TOKEN_LIFETIME_MINUTES,
        )

        db.session.commit()
        current_app.logger.info("Password reset requested user_id=%s token_id=%s", user.id, reset_token.id)
        return generic_result

    @staticmethod
    def validate_password_reset_token(raw_token):
        """Valider un token de reset sans l'utiliser."""
        reset_token = PasswordResetToken.find_by_raw_token(raw_token)
        if not reset_token:
            return {"error": "Lien invalide"}
        if reset_token.is_used:
            return {"error": "Ce lien a deja ete utilise"}
        if reset_token.is_expired:
            return {"error": "Ce lien a expire"}
        if not reset_token.user or not reset_token.user.is_active:
            return {"error": "Compte indisponible"}
        return {"success": True, "token": reset_token}

    @staticmethod
    def confirm_password_reset(raw_token, new_password):
        """Confirmer le reset et changer le mot de passe."""
        validation = AuthService.validate_password_reset_token(raw_token)
        if 'error' in validation:
            return validation

        reset_token = validation['token']
        user = reset_token.user
        user.set_password(new_password)
        reset_token.mark_used()

        PasswordResetToken.query.filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.id != reset_token.id,
            PasswordResetToken.used_at.is_(None),
        ).update({PasswordResetToken.used_at: datetime.utcnow()})

        db.session.commit()
        return {"success": True, "message": "Mot de passe reinitialise avec succes"}

    # ✅ NOUVEAU : Méthode pour créer un admin (usage interne uniquement)
    @staticmethod
    def create_admin_user(username, email, password):
        """Créer un utilisateur admin (usage interne/script uniquement)"""
        if User.query.filter_by(role='Admin').first():
            return {"error": "Un administrateur existe déjà"}

        user = User(
            username=username,
            email=email,
            role='Admin',
            is_verified=True  # Admin vérifié automatiquement
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return {"success": True, "user": user}

    @staticmethod
    def update_profile(user_id, username=None, email=None, password=None):
        """Mettre a jour le profil utilisateur."""
        user = User.query.get_or_404(user_id)

        if username and username != user.username:
            existing_username = User.query.filter_by(username=username).first()
            if existing_username and existing_username.id != user.id:
                return {"error": "Ce nom d'utilisateur existe deja"}
            user.username = username

        if email and email != user.email:
            existing_email = User.query.filter_by(email=email).first()
            if existing_email and existing_email.id != user.id:
                return {"error": "Cet email est deja utilise"}
            user.email = email
            user.is_verified = False
            verification = EmailVerification.create_verification(user.id)
            verification_url = url_for('auth.verify_email', token=verification.token, _external=True)
            EmailService.send_verification_email(user.email, user.username, verification_url)

        if password:
            user.set_password(password)

        db.session.commit()
        return {"success": True, "user": user}
