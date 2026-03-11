"""Modèles liés aux arcs narratifs des campagnes"""
from datetime import datetime
from app.extensions import db


class StoryArc(db.Model):
    """Modèle pour un arc narratif d'une campagne"""
    id = db.Column(db.Integer, primary_key=True)

    # Relation avec la campagne
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)

    # Informations de base
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    # Ordre dans la campagne
    order_index = db.Column(db.Integer, default=0)

    # Statuts
    status = db.Column(db.String(20), default='à_venir')  # à_venir, en_cours, terminé

    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Métadonnées
    estimated_sessions = db.Column(db.Integer, default=1)
    notes = db.Column(db.Text)

    # Relations
    campaign = db.relationship('Campaign', backref=db.backref('story_arcs', lazy=True, order_by='StoryArc.order_index'))

    @property
    def is_current(self):
        """Vérifier si c'est l'arc en cours"""
        return self.status == 'en_cours'

    @property
    def is_completed(self):
        """Vérifier si l'arc est terminé"""
        return self.status == 'terminé'

    @property
    def can_be_started(self):
        """Vérifier si l'arc peut être démarré"""
        return self.status == 'à_venir'

    def __repr__(self):
        return f'<StoryArc {self.name} ({self.status})>'