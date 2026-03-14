"""Modèle des notifications utilisateur."""
from datetime import datetime

from app.extensions import db


class Notification(db.Model):
    """Notification persistée visible dans le centre de notifications."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=True, index=True)

    title = db.Column(db.String(160), nullable=False)
    message = db.Column(db.Text, nullable=False)
    kind = db.Column(db.String(60), nullable=False, default='general', index=True)

    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True, cascade='all, delete-orphan'))
    campaign = db.relationship('Campaign')

    def __repr__(self):
        return f'<Notification {self.kind} user={self.user_id}>'
