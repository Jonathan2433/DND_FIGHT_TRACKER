"""Modèles liés aux campagnes"""
from datetime import datetime
from app.extensions import db


class Campaign(db.Model):
    """Modèle pour une campagne D&D"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    # Propriétaire (MJ)
    mj_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations
    mj = db.relationship('User', backref=db.backref('owned_campaigns', lazy=True))
    members = db.relationship('CampaignMember', backref='campaign', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Campaign {self.name}>'


class CampaignMember(db.Model):
    """Table d'association pour les membres d'une campagne"""
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations
    user = db.relationship('User')

    # Index unique pour éviter les doublons
    __table_args__ = (db.UniqueConstraint('campaign_id', 'user_id'),)


class CampaignInvitation(db.Model):
    """Invitations à rejoindre une campagne"""
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    invited_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Si utilisateur existe
    invited_email = db.Column(db.String(120), nullable=True)  # Si utilisateur n'existe pas encore

    # Token pour accepter l'invitation
    token = db.Column(db.String(255), unique=True, nullable=False)

    # Status
    is_accepted = db.Column(db.Boolean, default=False)
    is_declined = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    # Relations
    campaign = db.relationship('Campaign')
    invited_user = db.relationship('User')

    @staticmethod
    def generate_token():
        """Générer un token sécurisé"""
        import secrets
        return secrets.token_urlsafe(32)


class JoinRequest(db.Model):
    """Demandes pour rejoindre une campagne"""
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text)  # Message du demandeur

    # Status
    is_pending = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False)
    is_rejected = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_public = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations
    campaign = db.relationship('Campaign')
    user = db.relationship('User')

    # Index unique pour éviter les demandes multiples
    __table_args__ = (db.UniqueConstraint('campaign_id', 'user_id'),)