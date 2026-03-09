"""Service métier pour la gestion de l'expérience"""
from app.extensions import db
from app.models import CharacterTemplate, Combat, CombatLog
from app.models.experience import XPLog


class XPService:
    """Service pour la gestion de l'expérience"""

    # Tables de référence D&D 5e
    XP_TABLE = {
        1: 0, 2: 300, 3: 900, 4: 2700, 5: 6500,
        6: 14000, 7: 23000, 8: 34000, 9: 48000, 10: 64000,
        11: 85000, 12: 100000, 13: 120000, 14: 140000, 15: 165000,
        16: 195000, 17: 225000, 18: 265000, 19: 305000, 20: 355000
    }

    MONSTER_XP = {
        0: 10, 0.125: 25, 0.25: 50, 0.5: 100,
        1: 200, 2: 450, 3: 700, 4: 1100, 5: 1800,
        6: 2300, 7: 2900, 8: 3900, 9: 5000, 10: 5900,
        11: 7200, 12: 8400, 13: 10000, 14: 11500, 15: 13000
    }

    @staticmethod
    def award_xp(character_id, xp_amount, source="manual", description="", combat_id=None, awarded_by="DM"):
        """Attribuer de l'XP à un personnage"""
        character = CharacterTemplate.query.get_or_404(character_id)
        level_before = character.level

        # Ajouter l'XP
        character.current_xp += xp_amount

        # Vérifier montée de niveau
        level_after = XPService.calculate_level_from_xp(character.current_xp)
        if level_after > character.level:
            character.level = level_after

        # Log de l'attribution
        xp_log = XPLog(
            character_id=character_id,
            combat_id=combat_id,
            xp_amount=xp_amount,
            xp_source=source,
            description=description,
            level_before=level_before,
            level_after=character.level,
            awarded_by=awarded_by
        )

        db.session.add(xp_log)
        db.session.commit()

        return {
            'character': character,
            'leveled_up': level_after > level_before,
            'new_level': character.level,
            'total_xp': character.current_xp
        }

    @staticmethod
    def calculate_level_from_xp(total_xp):
        """Calculer le niveau basé sur l'XP totale"""
        for level in range(20, 0, -1):  # De 20 à 1
            if total_xp >= XPService.XP_TABLE[level]:
                return level
        return 1

    @staticmethod
    def calculate_combat_xp(combat_id, party_size=4):
        """Calculer l'XP d'un combat basée sur les ennemis vaincus"""
        combat = Combat.query.get_or_404(combat_id)

        if not combat.is_closed:
            return 0

        total_xp = 0

        # XP des ennemis morts
        for combatant in combat.combatants:
            if combatant.type in ["Ennemi", "Boss"] and combatant.is_dead:
                # Estimation du CR basée sur les HP (très approximatif)
                estimated_cr = XPService.estimate_cr_from_stats(combatant.hp_max, combatant.ac_base)
                monster_xp = XPService.MONSTER_XP.get(estimated_cr, 100)
                total_xp += monster_xp

        # Diviser par le nombre de PJ
        pj_count = len([c for c in combat.combatants if c.type == "PJ"])
        if pj_count > 0:
            xp_per_character = total_xp // pj_count
        else:
            xp_per_character = total_xp // party_size

        return xp_per_character

    @staticmethod
    def estimate_cr_from_stats(hp, ac):
        """Estimer le CR d'un monstre basé sur ses stats (approximatif)"""
        # Estimation très basique - vous pouvez l'améliorer
        if hp <= 10:
            return 0.125
        elif hp <= 20:
            return 0.25
        elif hp <= 35:
            return 0.5
        elif hp <= 50:
            return 1
        elif hp <= 70:
            return 2
        elif hp <= 100:
            return 3
        elif hp <= 130:
            return 4
        else:
            return 5

    @staticmethod
    def get_character_xp_history(character_id):
        """Récupérer l'historique d'XP d'un personnage"""
        return XPLog.query.filter_by(character_id=character_id).order_by(XPLog.timestamp.desc()).all()

    @staticmethod
    def award_combat_xp_to_party(combat_id, awarded_by="DM"):
        """Attribuer automatiquement l'XP de combat à tous les PJ participants"""
        combat = Combat.query.get_or_404(combat_id)

        if not combat.is_closed:
            return {"error": "Combat not closed"}

        # Trouver tous les PJ du combat
        party_members = [c for c in combat.combatants if c.type == "PJ"]

        if not party_members:
            return {"error": "No player characters found"}

        # Calculer l'XP du combat
        xp_per_character = XPService.calculate_combat_xp(combat_id, len(party_members))

        results = []
        for pj in party_members:
            # Trouver le template correspondant
            character = CharacterTemplate.query.filter_by(name=pj.name).first()
            if character:
                result = XPService.award_xp(
                    character.id,
                    xp_per_character,
                    source="combat",
                    description=f"Combat: {combat.name}",
                    combat_id=combat_id,
                    awarded_by=awarded_by
                )
                results.append(result)

        return {
            "success": True,
            "xp_awarded": xp_per_character,
            "characters": results
        }