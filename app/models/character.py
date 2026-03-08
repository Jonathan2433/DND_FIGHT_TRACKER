"""Modèles liés aux personnages"""
from datetime import datetime
from app.extensions import db


class CharacterTemplate(db.Model):
    """Template de personnage réutilisable"""
    id = db.Column(db.Integer, primary_key=True)

    # Identité
    name = db.Column(db.String(100), nullable=False)
    character_class = db.Column(db.String(50))
    level = db.Column(db.Integer, default=1)
    notes = db.Column(db.Text)

    # Combat de base
    hp_max = db.Column(db.Integer, nullable=False)
    ac_base = db.Column(db.Integer, nullable=False)
    initiative_bonus = db.Column(db.Integer, default=0)

    # Caractéristiques principales
    force = db.Column(db.Integer, default=10)
    dexterite = db.Column(db.Integer, default=10)
    constitution = db.Column(db.Integer, default=10)
    intelligence = db.Column(db.Integer, default=10)
    sagesse = db.Column(db.Integer, default=10)
    charisme = db.Column(db.Integer, default=10)

    # Maîtrises de sauvegarde
    maitrise_force = db.Column(db.Boolean, default=False)
    maitrise_dexterite = db.Column(db.Boolean, default=False)
    maitrise_constitution = db.Column(db.Boolean, default=False)
    maitrise_intelligence = db.Column(db.Boolean, default=False)
    maitrise_sagesse = db.Column(db.Boolean, default=False)
    maitrise_charisme = db.Column(db.Boolean, default=False)

    # Fichiers
    image_filename = db.Column(db.String(255), nullable=True)
    pdf_filename = db.Column(db.String(255), nullable=True)

    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Propriétés calculées - Modificateurs
    @property
    def mod_force(self):
        """Modificateur de Force"""
        return (self.force - 10) // 2

    @property
    def mod_dexterite(self):
        """Modificateur de Dextérité"""
        return (self.dexterite - 10) // 2

    @property
    def mod_constitution(self):
        """Modificateur de Constitution"""
        return (self.constitution - 10) // 2

    @property
    def mod_intelligence(self):
        """Modificateur d'Intelligence"""
        return (self.intelligence - 10) // 2

    @property
    def mod_sagesse(self):
        """Modificateur de Sagesse"""
        return (self.sagesse - 10) // 2

    @property
    def mod_charisme(self):
        """Modificateur de Charisme"""
        return (self.charisme - 10) // 2

    # Propriétés calculées - Bonus de maîtrise
    @property
    def bonus_maitrise(self):
        """Bonus de maîtrise basé sur le niveau"""
        if self.level <= 4:
            return 2
        elif self.level <= 8:
            return 3
        elif self.level <= 12:
            return 4
        elif self.level <= 16:
            return 5
        else:
            return 6

    # Propriétés calculées - Jets de sauvegarde
    @property
    def sauvegarde_force(self):
        """Jet de sauvegarde de Force"""
        bonus = self.bonus_maitrise if self.maitrise_force else 0
        return self.mod_force + bonus

    @property
    def sauvegarde_dexterite(self):
        """Jet de sauvegarde de Dextérité"""
        bonus = self.bonus_maitrise if self.maitrise_dexterite else 0
        return self.mod_dexterite + bonus

    @property
    def sauvegarde_constitution(self):
        """Jet de sauvegarde de Constitution"""
        bonus = self.bonus_maitrise if self.maitrise_constitution else 0
        return self.mod_constitution + bonus

    @property
    def sauvegarde_intelligence(self):
        """Jet de sauvegarde d'Intelligence"""
        bonus = self.bonus_maitrise if self.maitrise_intelligence else 0
        return self.mod_intelligence + bonus

    @property
    def sauvegarde_sagesse(self):
        """Jet de sauvegarde de Sagesse"""
        bonus = self.bonus_maitrise if self.maitrise_sagesse else 0
        return self.mod_sagesse + bonus

    @property
    def sauvegarde_charisme(self):
        """Jet de sauvegarde de Charisme"""
        bonus = self.bonus_maitrise if self.maitrise_charisme else 0
        return self.mod_charisme + bonus