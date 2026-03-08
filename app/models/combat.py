"""Modèles liés au combat"""
from datetime import datetime
from app.extensions import db


class Combat(db.Model):
    """Modèle pour un combat D&D"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    round = db.Column(db.Integer, default=1)
    current_turn = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_closed = db.Column(db.Boolean, default=False)

    # Relations
    combatants = db.relationship('Combatant', backref='combat', cascade="all, delete")

    # Gestion du temps
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    current_turn_start = db.Column(db.DateTime, nullable=True)
    current_round_start = db.Column(db.DateTime, nullable=True)
    has_started = db.Column(db.Boolean, default=False)


class Combatant(db.Model):
    """Modèle pour un combattant dans un combat"""
    id = db.Column(db.Integer, primary_key=True)
    combat_id = db.Column(db.Integer, db.ForeignKey('combat.id'), nullable=False)

    # Informations de base
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50))  # PJ, Ennemi, Boss, Neutre

    # Points de vie
    hp_max = db.Column(db.Integer, nullable=False)
    hp_current = db.Column(db.Integer, nullable=False)
    temp_hp = db.Column(db.Integer, default=0)

    # Combat
    initiative = db.Column(db.Integer, nullable=False)
    ac_base = db.Column(db.Integer, nullable=False)
    ac_bonus = db.Column(db.Integer, default=0)

    # États
    conditions = db.Column(db.String(255))
    is_dead = db.Column(db.Boolean, default=False)
    has_fled = db.Column(db.Boolean, default=False)
    is_hidden = db.Column(db.Boolean, default=False)

    # Groupes
    group_id = db.Column(db.Integer, nullable=True)
    is_group = db.Column(db.Boolean, default=False)
    group_name = db.Column(db.String(100), nullable=True)

    # Divers
    notes = db.Column(db.Text)

    @property
    def ac_total(self):
        """Calcul de la CA totale (base + bonus)"""
        return self.ac_base + (self.ac_bonus or 0)


class CombatLog(db.Model):
    """Log des actions de combat pour statistiques"""
    id = db.Column(db.Integer, primary_key=True)
    combat_id = db.Column(db.Integer, db.ForeignKey('combat.id'), nullable=False)

    # Acteurs
    actor_id = db.Column(db.Integer, nullable=True)  # Qui fait l'action
    target_id = db.Column(db.Integer, nullable=True)  # Qui subit l'action
    turn_owner_id = db.Column(db.Integer, nullable=True)  # À qui est le tour

    # Action
    action_type = db.Column(db.String(50), nullable=False)  # damage, heal, condition, ac_mod, etc.
    value = db.Column(db.Integer, nullable=True)  # Montant (dégâts, soins, etc.)
    detail = db.Column(db.String(255), nullable=True)  # Détails supplémentaires

    # Contexte temporel
    round_number = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    turn_duration = db.Column(db.Float, nullable=True)  # Durée en secondes