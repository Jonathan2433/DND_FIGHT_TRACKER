"""Modèles liés aux rencontres prédéfinies"""
from datetime import datetime
from app.extensions import db


class EncounterTemplate(db.Model):
    """Template de rencontre avec plusieurs ennemis"""
    id = db.Column(db.Integer, primary_key=True)

    # Sécurité et ownership
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Informations de base
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    difficulty = db.Column(db.String(50))  # Easy, Medium, Hard, Deadly

    # Données des combattants (stockées en JSON)
    combatants_json = db.Column(db.Text)

    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship('User', backref=db.backref('encounter_templates', lazy=True))
