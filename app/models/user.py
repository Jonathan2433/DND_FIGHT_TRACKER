"""Modèles liés aux utilisateurs et authentification"""
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from app.extensions import db


class User(db.Model):
    """Modèle utilisateur"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='Joueur')  # Admin, MJ, Joueur
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        """Hasher le mot de passe"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Vérifier le mot de passe"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class EmailVerification(db.Model):
    """Tokens de vérification email"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)

    @staticmethod
    def generate_token():
        """Générer un token sécurisé"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_verification(user_id):
        """Créer une nouvelle vérification"""
        token = EmailVerification.generate_token()
        expires_at = datetime.utcnow() + timedelta(hours=24)

        verification = EmailVerification(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )

        db.session.add(verification)
        db.session.commit()

        return verification

    @property
    def is_expired(self):
        """Vérifier si le token a expiré"""
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f'<EmailVerification {self.token[:8]}...>'