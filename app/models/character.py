"""Modèles liés aux personnages"""
from datetime import datetime
from app.extensions import db


class CharacterTemplate(db.Model):
    """Template de personnage réutilisable"""
    id = db.Column(db.Integer, primary_key=True)

    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=True)
    character_type = db.Column(db.String(20), default='PJ')  # PJ, PNJ, Boss
    is_shared = db.Column(db.Boolean, default=False)  # Pour les PNJ partagés par le MJ
    is_public = db.Column(db.Boolean, default=False)# ✅ NOUVEAU : Visible par tous
    is_active = db.Column(db.Boolean, default=False)

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

    # ✅ AJOUT : XP et progression
    current_xp = db.Column(db.Integer, default=0)

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

    # ✅ AJOUT : Propriétés XP
    @property
    def xp_for_next_level(self):
        """XP nécessaire pour le niveau suivant"""
        XP_TABLE = {
            1: 0, 2: 300, 3: 900, 4: 2700, 5: 6500,
            6: 14000, 7: 23000, 8: 34000, 9: 48000, 10: 64000,
            11: 85000, 12: 100000, 13: 120000, 14: 140000, 15: 165000,
            16: 195000, 17: 225000, 18: 265000, 19: 305000, 20: 355000
        }

        if self.level >= 20:
            return XP_TABLE[20]
        return XP_TABLE.get(self.level + 1, 355000)

    @property
    def xp_for_current_level(self):
        """XP nécessaire pour le niveau actuel"""
        XP_TABLE = {
            1: 0, 2: 300, 3: 900, 4: 2700, 5: 6500,
            6: 14000, 7: 23000, 8: 34000, 9: 48000, 10: 64000,
            11: 85000, 12: 100000, 13: 120000, 14: 140000, 15: 165000,
            16: 195000, 17: 225000, 18: 265000, 19: 305000, 20: 355000
        }
        return XP_TABLE.get(self.level, 0)

    @property
    def xp_progress_percentage(self):
        """Pourcentage de progression vers le niveau suivant"""
        if self.level >= 20:
            return 100

        xp_needed_for_next = self.xp_for_next_level - self.xp_for_current_level
        xp_current_progress = self.current_xp - self.xp_for_current_level

        if xp_needed_for_next <= 0:
            return 100

        return min(100, (xp_current_progress / xp_needed_for_next) * 100)

    @property
    def can_level_up(self):
        """Vérifier si le personnage peut monter de niveau"""
        return self.current_xp >= self.xp_for_next_level and self.level < 20

    def can_be_edited_by(self, user):
        """Vérifier si un utilisateur peut modifier ce personnage"""
        if not user:
            return False

        # Admin : peut tout modifier
        if user.role == 'Admin':
            return True

        # Propriétaire : peut toujours modifier ses personnages (même publics)
        if self.owner_id == user.id:
            return True

        # MJ de la campagne : peut modifier les personnages de sa campagne
        if self.campaign and user.is_mj_of(self.campaign):
            return True

        # ✅ CORRECTION : Un personnage public ne peut PAS être modifié par n'importe qui
        # La visibilité publique ne donne que le droit de VOIR, pas de MODIFIER

        return False