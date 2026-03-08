"""Service métier pour la gestion des groupes de combattants"""
from datetime import datetime
from app.extensions import db
from app.models import Combatant, CombatLog
from app.utils import get_current_actor


class GroupService:
    """Service pour la gestion des groupes de combattants"""

    @staticmethod
    def create_group(combatant_ids):
        """Créer un groupe à partir d'une liste de combattants"""
        if len(combatant_ids) < 2:
            return None

        # Récupérer uniquement les combattants vivants
        combatants = Combatant.query.filter(
            Combatant.id.in_(combatant_ids),
            Combatant.is_dead == False
        ).all()

        if len(combatants) < 2:
            return None

        group_id = int(datetime.utcnow().timestamp())
        group_name = combatants[0].name.split(" ")[0]

        for c in combatants:
            c.group_id = group_id
            c.group_name = group_name
            c.is_group = True

        db.session.commit()

        return group_id

    @staticmethod
    def ungroup(group_id):
        """Défaire un groupe"""
        combatants = Combatant.query.filter_by(group_id=group_id).all()

        if not combatants:
            return None

        for c in combatants:
            c.group_id = None
            c.group_name = None
            c.is_group = False

        db.session.commit()

        return combatants[0].combat_id

    @staticmethod
    def apply_group_damage(group_id, amount):
        """Appliquer des dégâts à tous les membres d'un groupe"""
        members = Combatant.query.filter_by(group_id=group_id).all()

        if not members:
            return None

        combat = members[0].combat
        actor = get_current_actor(combat)

        for c in members:
            c.hp_current -= amount

            if c.hp_current <= 0:
                c.hp_current = 0
                c.is_dead = True

            # Log individuel
            log = CombatLog(
                combat_id=combat.id,
                actor_id=actor.id if actor else None,
                target_id=c.id,
                turn_owner_id=actor.id if actor else None,
                action_type="damage",
                value=amount,
                round_number=combat.round
            )
            db.session.add(log)

        db.session.commit()

        return combat.id

    @staticmethod
    def apply_group_heal(group_id, amount):
        """Appliquer des soins à tous les membres d'un groupe"""
        members = Combatant.query.filter_by(group_id=group_id).all()

        if not members:
            return None

        combat = members[0].combat
        actor = get_current_actor(combat)

        for c in members:
            c.hp_current += amount

            if c.hp_current > c.hp_max:
                c.hp_current = c.hp_max

            if c.hp_current > 0:
                c.is_dead = False

            # Log individuel
            log = CombatLog(
                combat_id=combat.id,
                actor_id=actor.id if actor else None,
                target_id=c.id,
                turn_owner_id=actor.id if actor else None,
                action_type="heal",
                value=amount,
                round_number=combat.round
            )
            db.session.add(log)

        db.session.commit()

        return combat.id

    @staticmethod
    def toggle_group_condition(group_id, condition):
        """Basculer une condition pour tous les membres d'un groupe"""
        members = Combatant.query.filter_by(group_id=group_id).all()

        if not members:
            return None

        combat = members[0].combat
        actor = get_current_actor(combat)

        for c in members:
            current_conditions = c.conditions.split(",") if c.conditions else []

            if condition in current_conditions:
                current_conditions.remove(condition)
                action_detail = f"remove:{condition}"
            else:
                current_conditions.append(condition)
                action_detail = f"apply:{condition}"

            c.conditions = ",".join(current_conditions)

            # Log individuel
            log = CombatLog(
                combat_id=combat.id,
                actor_id=actor.id if actor else None,
                target_id=c.id,
                turn_owner_id=actor.id if actor else None,
                action_type="condition",
                detail=action_detail,
                round_number=combat.round
            )
            db.session.add(log)

        db.session.commit()

        return combat.id