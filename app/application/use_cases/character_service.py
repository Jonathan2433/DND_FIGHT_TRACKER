"""Application use cases (migrated from legacy services)."""

# app/services/character_service.py - CRÉER CE FICHIER
from app.extensions import db
from app.models import CharacterTemplate, Campaign, User


class CharacterService:
    """Service dédié pour la gestion des personnages selon les règles métier"""

    @staticmethod
    def create_character(owner_id, **kwargs):
        """Créer un nouveau personnage"""
        character_data = kwargs.copy()
        character_data['owner_id'] = owner_id
        hp_max = int(character_data.get('hp_max', 1))
        character_data.setdefault('hp_max', hp_max)
        character_data.setdefault('hp_current', hp_max)
        character_data.setdefault('ac_bonus', 0)

        character = CharacterTemplate(**character_data)
        db.session.add(character)
        db.session.commit()

        return character

    @staticmethod
    def create_pnj(creator_id, campaign_id, **kwargs):
        """Créer un PNJ (MJ uniquement)"""
        creator = User.query.get_or_404(creator_id)
        campaign = Campaign.query.get_or_404(campaign_id)

        # Vérifier que c'est bien le MJ de la campagne
        if not creator.is_mj_of(campaign):
            raise ValueError("Seul le MJ peut créer des PNJ")

        # Préparer les données sans conflit
        pnj_data = {
            'owner_id': creator_id,
            'character_type': 'PNJ',
            'campaign_id': campaign_id,
        }

        # Ajouter tous les autres paramètres
        pnj_data.update(kwargs)
        hp_max = int(pnj_data.get('hp_max', 1))
        pnj_data.setdefault('hp_max', hp_max)
        pnj_data.setdefault('hp_current', hp_max)
        pnj_data.setdefault('ac_bonus', 0)

        pnj = CharacterTemplate(**pnj_data)

        db.session.add(pnj)
        db.session.commit()

        return pnj
