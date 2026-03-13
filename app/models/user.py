"""Modeles lies aux utilisateurs et authentification."""
from datetime import datetime, timedelta
import secrets

from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class User(db.Model):
    """Modele utilisateur."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='Joueur')  # Admin, MJ, Joueur, MJ+Joueur
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    campaign_memberships = db.relationship('CampaignMember', backref='member_user', lazy=True)

    def set_password(self, password):
        """Hasher le mot de passe."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifier le mot de passe."""
        return check_password_hash(self.password_hash, password)

    def get_campaigns(self):
        """Recuperer toutes les campagnes de l'utilisateur."""
        from app.models.campaign import Campaign

        owned = Campaign.query.filter_by(mj_id=self.id, is_active=True).all()
        memberships = [m.campaign for m in self.campaign_memberships if m.campaign.is_active]
        all_campaigns = list(set(owned + memberships))
        return sorted(all_campaigns, key=lambda c: c.created_at, reverse=True)

    def is_mj_of(self, campaign):
        """Verifier si l'utilisateur est MJ d'une campagne."""
        return campaign.mj_id == self.id

    def is_member_of(self, campaign):
        """Verifier si l'utilisateur est membre d'une campagne."""
        from app.models.campaign import CampaignMember

        membership = CampaignMember.query.filter_by(
            campaign_id=campaign.id,
            user_id=self.id,
        ).first()
        return membership is not None

    def can_access_campaign(self, campaign):
        """Verifier si l'utilisateur peut acceder a une campagne."""
        return self.is_mj_of(campaign) or self.is_member_of(campaign) or self.role == 'Admin'

    def has_mj_capability(self):
        """Capacite MJ: role explicite, admin, ou possession d'une campagne."""
        if self.role in ['Admin', 'MJ', 'MJ+Joueur']:
            return True
        return len(self.owned_campaigns) > 0

    def has_player_capability(self):
        """Capacite joueur: role explicite, admin, ou participation a une campagne."""
        if self.role in ['Admin', 'Joueur', 'MJ+Joueur', 'MJ']:
            return True
        return len(self.campaign_memberships) > 0

    def __repr__(self):
        return f'<User {self.username}>'


class EmailVerification(db.Model):
    """Tokens de verification email."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)

    @staticmethod
    def generate_token():
        """Generer un token securise."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_verification(user_id):
        """Creer une nouvelle verification."""
        token = EmailVerification.generate_token()
        expires_at = datetime.utcnow() + timedelta(hours=24)

        verification = EmailVerification(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )

        db.session.add(verification)
        db.session.commit()

        return verification

    @property
    def is_expired(self):
        """Verifier si le token a expire."""
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f'<EmailVerification {self.token[:8]}...>'
