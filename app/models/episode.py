"""Modeles lies aux episodes d'un arc narratif."""
from datetime import datetime

from app.extensions import db


class Episode(db.Model):
    """Episode d'arc narratif."""

    id = db.Column(db.Integer, primary_key=True)
    story_arc_id = db.Column(db.Integer, db.ForeignKey('story_arc.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    summary_shared = db.Column(db.Text)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    story_arc = db.relationship('StoryArc', backref=db.backref('episodes', lazy=True, order_by='Episode.order_index'))


class EpisodeUserNote(db.Model):
    """Notes personnelles par episode et par utilisateur."""

    id = db.Column(db.Integer, primary_key=True)
    episode_id = db.Column(db.Integer, db.ForeignKey('episode.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notes = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    episode = db.relationship('Episode', backref=db.backref('user_notes', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('episode_notes', lazy=True, cascade='all, delete-orphan'))

    __table_args__ = (
        db.UniqueConstraint('episode_id', 'user_id', name='uq_episode_note_episode_user'),
    )
