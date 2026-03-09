"""Modèles liés à l'expérience"""
from datetime import datetime
from app.extensions import db


class XPLog(db.Model):
    """Log des gains d'XP pour traçabilité"""
    id = db.Column(db.Integer, primary_key=True)

    # Relation
    character_id = db.Column(db.Integer, db.ForeignKey('character_template.id'), nullable=False)
    combat_id = db.Column(db.Integer, db.ForeignKey('combat.id'), nullable=True)

    # XP
    xp_amount = db.Column(db.Integer, nullable=False)
    xp_source = db.Column(db.String(50), nullable=False)  # combat, quest, roleplay, exploration
    description = db.Column(db.Text)

    # Niveau avant/après pour tracking
    level_before = db.Column(db.Integer)
    level_after = db.Column(db.Integer)

    # Métadonnées
    awarded_by = db.Column(db.String(100))  # DM name
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)