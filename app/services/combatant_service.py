"""Service métier pour la gestion des combattants"""
from datetime import datetime
from app.extensions import db
from app.models import Combat, Combatant, CombatLog
from app.utils import get_current_actor


class CombatantService:
    """Service pour les actions sur les combattants"""

    @staticmethod
    def add_combatant(combat_id, name, type, hp_max, hp_current, initiative, ac_base):
        """Ajouter un nouveau combattant"""
        combat = Combat.query.get(combat_id)

        # Ajustement de l'index si le combat a déjà commencé
        if combat.has_started:
            combatants = sorted(
                [c for c in combat.combatants if not c.is_hidden],
                key=lambda x: x.initiative,
                reverse=True
            )
            if combat.current_turn >= len(combatants):
                combat.current_turn = 0

        if hp_current is None or hp_current == "":
            hp_current = hp_max

        combatant = Combatant(
            name=name,
            type=type,
            hp_max=int(hp_max),
            hp_current=int(hp_current),
            initiative=int(initiative),
            ac_base=int(ac_base),
            ac_bonus=0,
            conditions="",
            combat_id=combat_id
        )

        db.session.add(combatant)
        db.session.commit()

        return combatant

    @staticmethod
    def delete_combatant(combatant_id):
        """Supprimer un combattant et ses logs"""
        combatant = Combatant.query.get_or_404(combatant_id)
        combat_id = combatant.combat_id

        # Supprimer les logs liés
        CombatLog.query.filter(
            (CombatLog.actor_id == combatant_id) |
            (CombatLog.target_id == combatant_id)
        ).delete(synchronize_session=False)

        db.session.delete(combatant)
        db.session.commit()

        return combat_id

    @staticmethod
    def apply_damage(combatant_id, amount):
        """Appliquer des dégâts à un combattant"""
        combatant = Combatant.query.get_or_404(combatant_id)
        combat = combatant.combat
        actor = get_current_actor(combat)

        # Appliquer d'abord aux PV temporaires
        damage_to_temp = min(combatant.temp_hp, amount)
        combatant.temp_hp -= damage_to_temp

        # Le reste aux PV normaux
        remaining_damage = amount - damage_to_temp
        if remaining_damage > 0:
            combatant.hp_current -= remaining_damage
            if combatant.hp_current <= 0:
                combatant.hp_current = 0
                combatant.is_dead = True

        # Log de l'action
        log = CombatLog(
            combat_id=combat.id,
            actor_id=actor.id if actor else None,
            target_id=combatant.id,
            turn_owner_id=actor.id if actor else None,
            action_type="damage",
            value=amount,
            round_number=combat.round
        )

        db.session.add(log)
        db.session.commit()

        return combatant

    @staticmethod
    def apply_heal(combatant_id, amount):
        """Appliquer des soins à un combattant"""
        combatant = Combatant.query.get_or_404(combatant_id)
        combat = combatant.combat
        actor = get_current_actor(combat)

        combatant.hp_current += amount

        # Ne pas dépasser le max
        if combatant.hp_current > combatant.hp_max:
            combatant.hp_current = combatant.hp_max

        # Si le combattant était mort à 0 HP → il revient
        if combatant.hp_current > 0:
            combatant.is_dead = False

        # Log de l'action
        log = CombatLog(
            combat_id=combat.id,
            actor_id=actor.id if actor else None,
            target_id=combatant.id,
            turn_owner_id=actor.id if actor else None,
            action_type="heal",
            value=amount,
            round_number=combat.round
        )

        db.session.add(log)
        db.session.commit()

        return combatant

    @staticmethod
    def modify_ac(combatant_id, amount):
        """Modifier la CA d'un combattant"""
        combatant = Combatant.query.get_or_404(combatant_id)
        combat = combatant.combat
        actor = get_current_actor(combat)

        combatant.ac_bonus += amount

        # Log de l'action
        log = CombatLog(
            combat_id=combat.id,
            actor_id=actor.id if actor else None,
            target_id=combatant.id,
            turn_owner_id=actor.id if actor else None,
            action_type="ac_mod",
            value=amount,
            round_number=combat.round
        )

        db.session.add(log)
        db.session.commit()

        return combatant

    @staticmethod
    def modify_temp_hp(combatant_id, amount):
        """Modifier les PV temporaires"""
        combatant = Combatant.query.get_or_404(combatant_id)
        combat = combatant.combat
        actor = get_current_actor(combat)

        # Si nouveau montant supérieur, on remplace
        if amount > combatant.temp_hp:
            combatant.temp_hp = amount

        # Log de l'action
        log = CombatLog(
            combat_id=combat.id,
            actor_id=actor.id if actor else None,
            target_id=combatant.id,
            turn_owner_id=actor.id if actor else None,
            action_type="temp_hp",
            value=amount,
            round_number=combat.round
        )

        db.session.add(log)
        db.session.commit()

        return combatant

    @staticmethod
    def toggle_condition(combatant_id, condition):
        """Basculer une condition sur un combattant"""
        combatant = Combatant.query.get_or_404(combatant_id)
        combat = combatant.combat
        actor = get_current_actor(combat)

        current_conditions = combatant.conditions.split(",") if combatant.conditions else []

        if condition in current_conditions:
            current_conditions.remove(condition)
            action_detail = f"remove:{condition}"
        else:
            current_conditions.append(condition)
            action_detail = f"apply:{condition}"

        combatant.conditions = ",".join(current_conditions)

        # Log de l'action
        log = CombatLog(
            combat_id=combat.id,
            actor_id=actor.id if actor else None,
            target_id=combatant.id,
            turn_owner_id=actor.id if actor else None,
            action_type="condition",
            detail=action_detail,
            round_number=combat.round
        )

        db.session.add(log)
        db.session.commit()

        return combatant

    @staticmethod
    def toggle_visibility(combatant_id):
        """Basculer la visibilité d'un combattant"""
        combatant = Combatant.query.get_or_404(combatant_id)
        combatant.is_hidden = not combatant.is_hidden
        db.session.commit()

        return combatant

    @staticmethod
    def toggle_fled_status(combatant_id):
        """Basculer l'état de fuite d'un combattant"""
        combatant = Combatant.query.get_or_404(combatant_id)
        combat = combatant.combat
        actor = get_current_actor(combat)

        combatant.has_fled = not combatant.has_fled

        action_detail = "fled" if combatant.has_fled else "returned"

        log = CombatLog(
            combat_id=combat.id,
            actor_id=actor.id if actor else None,
            target_id=combatant.id,
            turn_owner_id=actor.id if actor else None,
            action_type="status",
            detail=action_detail,
            round_number=combat.round
        )

        db.session.add(log)
        db.session.commit()

        return combatant