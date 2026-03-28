"""Modèles de suivi d'activité du site."""
from datetime import datetime

from app.extensions import db


class SiteActivityLog(db.Model):
    """Journal technique des requêtes HTTP."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)

    path = db.Column(db.String(255), nullable=False, index=True)
    method = db.Column(db.String(10), nullable=False)
    endpoint = db.Column(db.String(120), nullable=True, index=True)

    status_code = db.Column(db.Integer, nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = db.relationship('User', backref=db.backref('site_activity_logs', lazy=True))

    def __repr__(self):
        return f'<SiteActivityLog {self.method} {self.path} [{self.status_code}]>'
