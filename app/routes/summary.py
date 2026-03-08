"""Routes pour les résumés de combat"""
from flask import Blueprint, render_template
from app.models import Combat, CombatLog

# Créer le blueprint
bp = Blueprint('summary', __name__, url_prefix='/summary')


@bp.route('/combat/<int:combat_id>')
def combat_summary(combat_id):
    """Résumé détaillé d'un combat"""
    combat = Combat.query.get_or_404(combat_id)
    logs = CombatLog.query.filter_by(
        combat_id=combat_id
    ).order_by(CombatLog.timestamp).all()

    # Durée totale du combat (format MM:SS)
    if combat.start_time and combat.end_time:
        total_seconds = int(
            (combat.end_time - combat.start_time).total_seconds()
        )
        total_duration = f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"
    else:
        total_duration = "00:00"

    # Statistiques générales
    total_rounds = combat.round
    total_deaths = len([c for c in combat.combatants if c.is_dead])
    total_fled = len([c for c in combat.combatants if c.has_fled])

    total_damage = sum(
        log.value or 0
        for log in logs
        if log.action_type == "damage"
    )

    total_heal = sum(
        log.value or 0
        for log in logs
        if log.action_type == "heal"
    )

    # Temps par round (format MM:SS)
    round_times = {}
    for log in logs:
        if log.action_type == "round_time":
            seconds = log.value
            round_times[log.round_number] = f"{seconds // 60:02d}:{seconds % 60:02d}"

    # Temps par tour (format MM:SS)
    combatant_lookup = {c.id: c.name for c in combat.combatants}
    turn_times = {}
    for log in logs:
        if log.action_type == "turn_time":
            seconds = log.value
            formatted_time = f"{seconds // 60:02d}:{seconds % 60:02d}"
            turn_times.setdefault(log.round_number, []).append({
                "actor": combatant_lookup.get(log.turn_owner_id, "Inconnu"),
                "duration": formatted_time
            })

    # Statistiques par combattant
    combatant_stats = []

    for c in combat.combatants:
        damage_done = sum(
            log.value or 0
            for log in logs
            if log.actor_id == c.id and log.action_type == "damage"
        )

        damage_taken = sum(
            log.value or 0
            for log in logs
            if log.target_id == c.id and log.action_type == "damage"
        )

        heal_done = sum(
            log.value or 0
            for log in logs
            if log.actor_id == c.id and log.action_type == "heal"
        )

        heal_taken = sum(
            log.value or 0
            for log in logs
            if log.target_id == c.id and log.action_type == "heal"
        )

        conditions_applied = len([
            log for log in logs
            if log.actor_id == c.id
               and log.action_type == "condition"
               and log.detail.startswith("apply:")
        ])

        conditions_received = len([
            log for log in logs
            if log.target_id == c.id
               and log.action_type == "condition"
               and log.detail.startswith("apply:")
        ])

        ac_bonus_given = sum(
            log.value or 0
            for log in logs
            if log.actor_id == c.id
            and log.action_type == "ac_mod"
        )

        # Temps total formaté en MM:SS
        time_seconds = sum(
            log.value or 0
            for log in logs
            if log.action_type == "turn_time"
            and log.turn_owner_id == c.id
        )

        time_formatted = f"{time_seconds // 60:02d}:{time_seconds % 60:02d}"

        combatant_stats.append({
            "name": c.name,
            "is_dead": c.is_dead,
            "has_fled": c.has_fled,
            "damage_done": damage_done,
            "damage_taken": damage_taken,
            "heal_done": heal_done,
            "heal_taken": heal_taken,
            "conditions_applied": conditions_applied,
            "conditions_received": conditions_received,
            "ac_bonus_given": ac_bonus_given,
            "time_spent": time_formatted
        })

    # Timeline structurée
    timeline = {}

    for log in logs:
        if log.action_type in ["round_time", "turn_time"]:
            continue

        round_number = log.round_number
        turn_owner = combatant_lookup.get(log.turn_owner_id, "Inconnu")
        actor = combatant_lookup.get(log.actor_id, "Inconnu")
        target = combatant_lookup.get(log.target_id, "Inconnu")

        timeline.setdefault(round_number, {})
        timeline[round_number].setdefault(turn_owner, [])

        if log.action_type == "damage":
            text = f"{actor} inflige {log.value} dégâts à {target}"
        elif log.action_type == "heal":
            text = f"{actor} soigne {log.value} PV à {target}"
        elif log.action_type == "condition":
            if log.detail.startswith("apply:"):
                condition = log.detail.split(":")[1]
                text = f"{actor} applique {condition} à {target}"
            else:
                condition = log.detail.split(":")[1]
                text = f"{actor} retire {condition} à {target}"
        elif log.action_type == "ac_mod":
            text = f"{actor} modifie la CA de {target} de {log.value:+d}"
        elif log.action_type == "status":
            if log.detail == "fled":
                text = f"{target} a pris la fuite"
            elif log.detail == "returned":
                text = f"{target} est revenu au combat"
            else:
                text = f"Statut de {target} modifié: {log.detail}"
        else:
            text = "Action inconnue"

        timeline[round_number][turn_owner].append(text)

    return render_template(
        "combat_summary.html",
        combat=combat,
        total_duration=total_duration,
        total_rounds=total_rounds,
        total_deaths=total_deaths,
        total_fled=total_fled,
        total_damage=total_damage,
        total_heal=total_heal,
        combatant_stats=combatant_stats,
        timeline=timeline,
        round_times=round_times,
        turn_times=turn_times
    )