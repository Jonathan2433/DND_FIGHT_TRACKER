"""Modèles liés aux personnages"""
from datetime import datetime
from app.extensions import db

# Table d'association many-to-many personnage-campagne
character_campaign_association = db.Table(
    'character_campaign_association',
    db.Column('character_id', db.Integer, db.ForeignKey('character_template.id')),
    db.Column('campaign_id', db.Integer, db.ForeignKey('campaign.id'))
)

class CharacterTemplate(db.Model):
    """Template de personnage réutilisable"""
    id = db.Column(db.Integer, primary_key=True)

    # Sécurité et associations
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=True)
    story_arc_id = db.Column(db.Integer, db.ForeignKey('story_arc.id'), nullable=True)
    character_type = db.Column(db.String(20), default='PJ')  # PJ, PNJ, Boss
    is_shared = db.Column(db.Boolean, default=False)  # Pour les PNJ partagés par le MJ
    is_public = db.Column(db.Boolean, default=False)  # Visible par tous
    visibility_level = db.Column(db.String(20), default='private')  # private, reduced, semi_complete, complete
    is_active = db.Column(db.Boolean, default=True)

    # Identité
    name = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(50))  # Prénom
    gender = db.Column(db.String(30))  # Genre affiche dans la fiche PDF
    player_name = db.Column(db.String(100))  # Nom du joueur
    campaign_name = db.Column(db.String(120))  # Nom de campagne pour la fiche PDF
    alignment = db.Column(db.String(60))  # Alignement DnD
    languages = db.Column(db.String(255))  # Langues parlées
    height = db.Column(db.String(60))  # Taille libre
    weight = db.Column(db.String(60))  # Poids libre
    eyes = db.Column(db.String(60))  # Couleur des yeux
    skin = db.Column(db.String(60))  # Teint/couleur de peau
    hair = db.Column(db.String(60))  # Couleur/coiffure
    equipment = db.Column(db.Text)  # Equipement principal pour la fiche
    skill_proficiencies = db.Column(db.String(255))  # Competences maitrisees (CSV)
    age = db.Column(db.Integer)  # Âge
    character_appearance = db.Column(db.Text)  # Zone "Character appearance"
    allies_organizations = db.Column(db.Text)  # Zone "Allies & Organizations"
    additional_features_traits = db.Column(db.Text)  # Zone "Additional Features & Traits"
    treasure = db.Column(db.Text)  # Zone "Treasure"
    symbol_name = db.Column(db.String(120))  # Nom dans le cartouche symbole (page 2)
    spellcasting_class = db.Column(db.String(80))  # Classe de lancement de sorts
    spellcasting_ability = db.Column(db.String(30))  # Caracteristique de lancement de sorts
    spell_save_dc = db.Column(db.Integer)  # DD de sauvegarde des sorts
    spell_attack_bonus = db.Column(db.Integer)  # Bonus d'attaque des sorts
    selected_cantrips = db.Column(db.Text)  # Sorts mineurs selectionnes (CSV)
    selected_level_1_spells = db.Column(db.Text)  # Sorts de niveau 1 selectionnes (CSV)
    background_story = db.Column(db.Text)  # Histoire/background
    character_class = db.Column(db.String(50))
    race = db.Column(db.String(50))
    level = db.Column(db.Integer, default=1)
    notes = db.Column(db.Text)
    private_notes = db.Column(db.Text)
    player_private_notes = db.Column(db.Text)
    personality_traits = db.Column(db.Text)
    ideals = db.Column(db.Text)
    bonds = db.Column(db.Text)
    flaws = db.Column(db.Text)
    inspiration = db.Column(db.Boolean, default=False)

    # Combat de base
    hp_max = db.Column(db.Integer, nullable=False)
    hp_current = db.Column(db.Integer, nullable=False)
    temp_hp = db.Column(db.Integer, default=0, nullable=False)
    ac_base = db.Column(db.Integer, nullable=False)
    ac_bonus = db.Column(db.Integer, default=0, nullable=False)
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

    # XP et progression
    current_xp = db.Column(db.Integer, default=0)

    # Fichiers
    image_filename = db.Column(db.String(255), nullable=True)
    pdf_filename = db.Column(db.String(255), nullable=True)

    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations
    owner = db.relationship('User', foreign_keys=[owner_id], backref=db.backref('owned_characters', lazy=True))
    campaign = db.relationship('Campaign', backref=db.backref('characters', lazy=True))
    story_arc = db.relationship('StoryArc', backref=db.backref('characters', lazy=True))
    campaigns = db.relationship('Campaign', secondary='character_campaign_association', backref='campaign_characters')

    # ========== PROPRIÉTÉS CALCULÉES (UNE SEULE FOIS) ==========

    # Modificateurs
    @property
    def hp_current_effective(self):
        """Points de vie courants (fallback au max pour anciens enregistrements)."""
        if self.hp_current is None:
            return self.hp_max
        return max(0, min(self.hp_current, self.hp_max))

    @property
    def ac_total(self):
        """Classe d'armure totale actuelle (base + bonus/malus)."""
        return self.ac_base + (self.ac_bonus or 0)

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

    # Bonus de maîtrise
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

    # Jets de sauvegarde
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

    # Propriétés XP
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

    # ========== MÉTHODES DE PERMISSIONS ==========

    def can_be_viewed_by(self, user, campaign=None):
        """Vérifier si un utilisateur peut voir ce personnage selon le niveau de visibilité"""
        campaign = campaign or self.campaign

        if not user:
            return bool(self.is_public)

        # Admin voit tout
        if user.role == 'Admin':
            return True

        # Propriétaire voit tout
        if self.owner_id == user.id:
            return True

        # MJ de campagne voit tout dans sa campagne
        if campaign and user.is_mj_of(campaign):
            return True

        if any(user.is_mj_of(c) for c in self.campaigns):
            return True

        if self.is_public:
            return True

        # Autres joueurs selon niveau de visibilité
        if self.visibility_level == 'private':
            return False
        elif self.visibility_level in ['reduced', 'semi_complete', 'complete']:
            # Doit être dans la même campagne
            if campaign:
                return user.is_member_of(campaign) and (
                    self.campaign_id == campaign.id or self in campaign.campaign_characters
                )
            if self.campaigns:
                return any(user.is_member_of(c) for c in self.campaigns)
            return False

        return False

    def can_be_edited_by(self, user, context='full'):
        """Vérifier si un utilisateur peut modifier ce personnage"""
        if not user:
            return False

        if user.role == 'Admin':
            return True

        # Propriétaire peut toujours tout modifier
        if self.owner_id == user.id:
            return True

        # ✅ NOUVEAU : MJ de campagne peut modifier les PJ de sa campagne
        if self.campaign and user.is_mj_of(self.campaign):
            # Si contexte précisé, on peut limiter ce que le MJ peut modifier
            return True

        if any(user.is_mj_of(c) for c in self.campaigns):
            # Si contexte précisé, on peut limiter ce que le MJ peut modifier
            return True

        return False

    # ========== PROPRIÉTÉS DE TYPE ==========

    @property
    def is_pj(self):
        return self.character_type == 'PJ'

    @property
    def is_pnj(self):
        return self.character_type == 'PNJ'

    # ========== MÉTHODES DE VISIBILITÉ ==========

    def get_visible_data(self, user, campaign=None):
        """Retourner les données visibles selon les permissions"""
        if not self.can_be_viewed_by(user, campaign):
            return None

        # Propriétaire, Admin ou MJ : données complètes
        if user and self.owner_id == user.id:
            return {
                'level': 'complete',
                'data': self._get_complete_data(include_private_notes=True, include_player_private_notes=True)
            }

        if user and user.role == 'Admin':
            return {
                'level': 'complete',
                'data': self._get_complete_data(include_private_notes=True, include_player_private_notes=False)
            }

        if user and (
            (campaign and user.is_mj_of(campaign))
            or any(user.is_mj_of(c) for c in self.campaigns)
        ):
            return {
                'level': 'complete',
                'data': self._get_complete_data(include_private_notes=True, include_player_private_notes=False)
            }

        # Selon niveau de visibilité
        if self.visibility_level == 'reduced':
            return {
                'level': 'reduced',
                'data': self._get_reduced_data()
            }
        elif self.visibility_level == 'semi_complete':
            return {
                'level': 'semi_complete',
                'data': self._get_semi_complete_data()
            }
        elif self.visibility_level == 'complete':
            return {
                'level': 'complete',
                'data': self._get_complete_data(include_private_notes=False, include_player_private_notes=False)
            }

        return None

    def _get_reduced_data(self):
        """Fiche réduite : nom, prénom, âge, photo"""
        return {
            'name': self.name,
            'first_name': self.first_name,
            'age': self.age,
            'image_filename': self.image_filename
        }

    def _get_semi_complete_data(self):
        """Fiche semi-complète : réduite + caractéristiques"""
        data = self._get_reduced_data()
        data.update({
            'character_class': self.character_class,
            'race': self.race,
            'level': self.level,
            'force': self.force,
            'dexterite': self.dexterite,
            'constitution': self.constitution,
            'intelligence': self.intelligence,
            'sagesse': self.sagesse,
            'charisme': self.charisme,
            'mod_force': self.mod_force,
            'mod_dexterite': self.mod_dexterite,
            'mod_constitution': self.mod_constitution,
            'mod_intelligence': self.mod_intelligence,
            'mod_sagesse': self.mod_sagesse,
            'mod_charisme': self.mod_charisme
        })
        return data

    def _get_complete_data(self, include_private_notes=True, include_player_private_notes=False):
        """Fiche complète : tout visible sauf notes privées selon contexte."""
        data = self._get_semi_complete_data()
        data.update({
            # Statistiques de combat
            'hp_max': self.hp_max,
            'hp_current': self.hp_current_effective,
            'temp_hp': max(0, self.temp_hp or 0),
            'ac_base': self.ac_base,
            'ac_bonus': self.ac_bonus or 0,
            'ac_total': self.ac_total,
            'initiative_bonus': self.initiative_bonus,

            # Maîtrises de sauvegarde
            'maitrise_force': self.maitrise_force,
            'maitrise_dexterite': self.maitrise_dexterite,
            'maitrise_constitution': self.maitrise_constitution,
            'maitrise_intelligence': self.maitrise_intelligence,
            'maitrise_sagesse': self.maitrise_sagesse,
            'maitrise_charisme': self.maitrise_charisme,

            # Sauvegardes calculées
            'sauvegarde_force': self.sauvegarde_force,
            'sauvegarde_dexterite': self.sauvegarde_dexterite,
            'sauvegarde_constitution': self.sauvegarde_constitution,
            'sauvegarde_intelligence': self.sauvegarde_intelligence,
            'sauvegarde_sagesse': self.sauvegarde_sagesse,
            'sauvegarde_charisme': self.sauvegarde_charisme,

            # Progression et notes
            'current_xp': self.current_xp,
            'xp_for_next_level': self.xp_for_next_level,
            'xp_for_current_level': self.xp_for_current_level,
            'xp_progress_percentage': self.xp_progress_percentage,
            'can_level_up': self.can_level_up,
            'bonus_maitrise': self.bonus_maitrise,

            # Histoire et notes (complètes pour le propriétaire/MJ)
            'notes': self.notes,
            'background_story': self.background_story,
            'alignment': self.alignment,
            'selected_cantrips': self.selected_cantrips,
            'selected_level_1_spells': self.selected_level_1_spells,

            # Fichiers
            'pdf_filename': self.pdf_filename,

            # Métadonnées
            'created_at': self.created_at,
            'character_type': self.character_type,
            'is_shared': self.is_shared,
            'is_public': self.is_public,
            'visibility_level': self.visibility_level
        })
        if include_private_notes:
            data['private_notes'] = self.private_notes

        if include_player_private_notes:
            data['player_private_notes'] = self.player_private_notes

        return data

    def __repr__(self):
        return f'<CharacterTemplate {self.name} ({self.character_type})>'

    def can_add_private_notes(self, user):
        """Vérifier si un utilisateur peut ajouter des notes privées"""
        if not user:
            return False

        # Admin peut tout faire
        if user.role == 'Admin':
            return True

        # ✅ NOUVEAU : MJ peut ajouter notes privées sur PJ de sa campagne
        if self.is_pj and self.campaign and user.is_mj_of(self.campaign):
            return True

        return False

    def get_private_notes_for_mj(self, mj_user):
        """Récupérer les notes privées du MJ pour ce pj"""
        if not self.can_add_private_notes(mj_user):
            return None

        # Pour l'instant, on utilise le champ private_notes existant
        # Plus tard, on pourrait créer une table séparée pour plusieurs MJ
        return self.private_notes
