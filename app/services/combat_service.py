"""Service métier pour la gestion des combats"""
from datetime import datetime
from app.extensions import db
from app.models import Combat, Combatant, CombatLog
from app.utils import get_current_actor


class CombatService:
    """Service principal pour la gestion des combats"""

    @staticmethod
    def create_combat(name):
        """Créer un nouveau combat"""
        combat = Combat(name=name)
        db.session.add(combat)
        db.session.commit()
        return combat

    @staticmethod
    def start_combat(combat_id):
        """Démarrer un combat"""
        combat = Combat.query.get_or_404(combat_id)

        if not combat.has_started:
            now = datetime.utcnow()
            combat.has_started = True
            combat.start_time = now
            combat.current_round_start = now
            combat.current_turn_start = now
            db.session.commit()

        return combat

    @staticmethod
    def close_combat(combat_id):
        """Clôturer un combat et finaliser les logs"""
        combat = Combat.query.get_or_404(combat_id)
        now = datetime.utcnow()

        # Finaliser dernier tour
        if combat.current_turn_start:
            turn_duration = (now - combat.current_turn_start).total_seconds()
            previous_actor = get_current_actor(combat)

            if previous_actor:
                log = CombatLog(
                    combat_id=combat.id,
                    actor_id=previous_actor.id,
                    turn_owner_id=previous_actor.id,
                    action_type="turn_time",
                    value=int(turn_duration),
                    round_number=combat.round,
                    turn_duration=turn_duration
                )
                db.session.add(log)

        # Finaliser dernier round
        if combat.current_round_start:
            round_duration = (now - combat.current_round_start).total_seconds()
            log = CombatLog(
                combat_id=combat.id,
                action_type="round_time",
                value=int(round_duration),
                round_number=combat.round
            )
            db.session.add(log)

        combat.end_time = now
        combat.is_closed = True
        db.session.commit()

        return combat

    @staticmethod
    def next_turn(combat_id):
        """Passer au tour suivant"""
        combat = Combat.query.get_or_404(combat_id)

        if not combat.has_started:
            return combat

        now = datetime.utcnow()

        # Calcul durée du tour précédent
        if combat.current_turn_start:
            previous_actor = get_current_actor(combat)

            if previous_actor:
                turn_duration = (now - combat.current_turn_start).total_seconds()

                log = CombatLog(
                    combat_id=combat.id,
                    actor_id=previous_actor.id,
                    turn_owner_id=previous_actor.id,
                    action_type="turn_time",
                    value=int(turn_duration),
                    round_number=combat.round,
                    turn_duration=turn_duration
                )
                db.session.add(log)

        # Avancer le tour
        combatants = sorted(
            [c for c in combat.combatants],
            key=lambda x: x.initiative,
            reverse=True
        )

        combat.current_turn += 1

        # Nouveau round si nécessaire
        if combat.current_turn >= len(combatants):
            if combat.current_round_start:
                round_duration = (now - combat.current_round_start).total_seconds()

                log = CombatLog(
                    combat_id=combat.id,
                    action_type="round_time",
                    value=int(round_duration),
                    round_number=combat.round
                )
                db.session.add(log)

            combat.current_turn = 0
            combat.round += 1
            combat.current_round_start = now

        combat.current_turn_start = now
        db.session.commit()

        return combat

    @staticmethod
    def get_combat_with_organized_data(combat_id):
        """Récupérer un combat avec ses données organisées"""
        combat = Combat.query.get_or_404(combat_id)

        combatants_sorted = sorted(
            [c for c in combat.combatants],
            key=lambda x: x.initiative,
            reverse=True
        )

        groups = {}
        singles = []

        for c in combatants_sorted:
            if c.is_hidden:
                continue

            if c.group_id:
                groups.setdefault(c.group_id, []).append(c)
            else:
                singles.append(c)

        # Calcul états des groupes
        group_condition_states = CombatService._calculate_group_condition_states(groups)

        # Ordre d'initiative pour le panneau
        initiative_order = sorted(
            [c for c in combat.combatants if not c.is_hidden],
            key=lambda x: x.initiative,
            reverse=True
        )

        return {
            'combat': combat,
            'groups': groups,
            'singles': singles,
            'group_condition_states': group_condition_states,
            'initiative_order': initiative_order
        }

    @staticmethod
    def _calculate_group_condition_states(groups):
        """Calculer les états de conditions pour les groupes"""
        from app.utils import CONDITIONS_LIST

        group_condition_states = {}

        for group_id, members in groups.items():
            group_condition_states[group_id] = {}

            for condition in CONDITIONS_LIST:
                count = 0
                for m in members:
                    if m.conditions and condition in m.conditions.split(","):
                        count += 1

                if count == 0:
                    state = "none"
                elif count == len(members):
                    state = "all"
                else:
                    state = "partial"

                group_condition_states[group_id][condition] = state

        return group_condition_states

    @staticmethod
    def delete_combat(combat_id):
        """Supprimer un combat et toutes ses données liées"""
        combat = Combat.query.get_or_404(combat_id)

        # Les relations cascade="all, delete" s'occupent automatiquement de :
        # - Supprimer tous les combattants
        # - Supprimer tous les logs (via les foreign keys)

        db.session.delete(combat)
        db.session.commit()

        return True