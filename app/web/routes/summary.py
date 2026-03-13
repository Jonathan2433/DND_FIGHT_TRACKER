"""Routes pour les resumes de combat et statistiques agregees."""
from flask import Blueprint, render_template, jsonify, g, flash, redirect, url_for

from app.models import Combat, CombatLog
from app.models.story_arc import StoryArc
from app.models.campaign import Campaign
from app.utils.decorators import login_required


bp = Blueprint('summary', __name__, url_prefix='/summary')


def _build_aggregate_stats(combats):
    combat_ids = [c.id for c in combats]
    logs = CombatLog.query.filter(CombatLog.combat_id.in_(combat_ids)).all() if combat_ids else []

    total_combats = len(combats)
    closed_combats = len([c for c in combats if c.is_closed])
    total_rounds = sum(c.round or 0 for c in combats)

    total_damage = sum((log.value or 0) for log in logs if log.action_type == 'damage')
    total_heal = sum((log.value or 0) for log in logs if log.action_type == 'heal')

    total_deaths = 0
    total_fled = 0
    for combat in combats:
        total_deaths += len([c for c in combat.combatants if c.is_dead])
        total_fled += len([c for c in combat.combatants if c.has_fled])

    durations = []
    for combat in combats:
        if combat.start_time and combat.end_time:
            durations.append(int((combat.end_time - combat.start_time).total_seconds()))

    avg_duration_seconds = int(sum(durations) / len(durations)) if durations else 0

    return {
        'total_combats': total_combats,
        'closed_combats': closed_combats,
        'total_rounds': total_rounds,
        'total_damage': total_damage,
        'total_heal': total_heal,
        'total_deaths': total_deaths,
        'total_fled': total_fled,
        'avg_duration_seconds': avg_duration_seconds,
    }


@bp.route('/combat/<int:combat_id>')
@login_required
def combat_summary(combat_id):
    """Resume detaille d'un combat."""
    combat = Combat.query.get_or_404(combat_id)

    if combat.campaign and not g.current_user.can_access_campaign(combat.campaign):
        flash('Acces interdit a ce combat.', 'error')
        return redirect(url_for('main.index'))

    logs = CombatLog.query.filter_by(combat_id=combat_id).order_by(CombatLog.timestamp).all()

    if combat.start_time and combat.end_time:
        total_seconds = int((combat.end_time - combat.start_time).total_seconds())
        total_duration = f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"
    else:
        total_duration = '00:00'

    total_rounds = combat.round
    total_deaths = len([c for c in combat.combatants if c.is_dead])
    total_fled = len([c for c in combat.combatants if c.has_fled])

    total_damage = sum(log.value or 0 for log in logs if log.action_type == 'damage')
    total_heal = sum(log.value or 0 for log in logs if log.action_type == 'heal')

    round_times = {}
    for log in logs:
        if log.action_type == 'round_time':
            seconds = log.value or 0
            round_times[log.round_number] = f"{seconds // 60:02d}:{seconds % 60:02d}"

    combatant_lookup = {c.id: c.name for c in combat.combatants}
    turn_times = {}
    for log in logs:
        if log.action_type == 'turn_time':
            seconds = log.value or 0
            formatted_time = f"{seconds // 60:02d}:{seconds % 60:02d}"
            turn_times.setdefault(log.round_number, []).append({
                'actor': combatant_lookup.get(log.turn_owner_id, 'Inconnu'),
                'duration': formatted_time,
            })

    combatant_stats = []
    for combatant in combat.combatants:
        damage_done = sum(log.value or 0 for log in logs if log.actor_id == combatant.id and log.action_type == 'damage')
        damage_taken = sum(log.value or 0 for log in logs if log.target_id == combatant.id and log.action_type == 'damage')
        heal_done = sum(log.value or 0 for log in logs if log.actor_id == combatant.id and log.action_type == 'heal')
        heal_taken = sum(log.value or 0 for log in logs if log.target_id == combatant.id and log.action_type == 'heal')
        conditions_applied = len([
            log for log in logs
            if log.actor_id == combatant.id and log.action_type == 'condition' and (log.detail or '').startswith('apply:')
        ])
        conditions_received = len([
            log for log in logs
            if log.target_id == combatant.id and log.action_type == 'condition' and (log.detail or '').startswith('apply:')
        ])
        ac_bonus_given = sum(log.value or 0 for log in logs if log.actor_id == combatant.id and log.action_type == 'ac_mod')
        time_seconds = sum(
            log.value or 0
            for log in logs
            if log.action_type == 'turn_time' and log.turn_owner_id == combatant.id
        )

        combatant_stats.append({
            'name': combatant.name,
            'is_dead': combatant.is_dead,
            'has_fled': combatant.has_fled,
            'damage_done': damage_done,
            'damage_taken': damage_taken,
            'heal_done': heal_done,
            'heal_taken': heal_taken,
            'conditions_applied': conditions_applied,
            'conditions_received': conditions_received,
            'ac_bonus_given': ac_bonus_given,
            'time_spent': f"{time_seconds // 60:02d}:{time_seconds % 60:02d}",
        })

    timeline = {}
    for log in logs:
        if log.action_type in ['round_time', 'turn_time']:
            continue

        round_number = log.round_number
        turn_owner = combatant_lookup.get(log.turn_owner_id, 'Inconnu')
        actor = combatant_lookup.get(log.actor_id, 'Inconnu')
        target = combatant_lookup.get(log.target_id, 'Inconnu')

        timeline.setdefault(round_number, {})
        timeline[round_number].setdefault(turn_owner, [])

        if log.action_type == 'damage':
            text = f"{actor} inflige {log.value} degats a {target}"
        elif log.action_type == 'heal':
            text = f"{actor} soigne {log.value} PV a {target}"
        elif log.action_type == 'condition':
            detail = log.detail or ''
            if detail.startswith('apply:'):
                condition = detail.split(':', 1)[1]
                text = f"{actor} applique {condition} a {target}"
            else:
                condition = detail.split(':', 1)[1] if ':' in detail else detail
                text = f"{actor} retire {condition} a {target}"
        elif log.action_type == 'ac_mod':
            text = f"{actor} modifie la CA de {target} de {log.value:+d}"
        elif log.action_type == 'status':
            if log.detail == 'fled':
                text = f"{target} a pris la fuite"
            elif log.detail == 'returned':
                text = f"{target} est revenu au combat"
            else:
                text = f"Statut de {target} modifie: {log.detail}"
        else:
            text = 'Action inconnue'

        timeline[round_number][turn_owner].append(text)

    return render_template(
        'combat_summary.html',
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
        turn_times=turn_times,
    )


@bp.route('/campaign/<int:campaign_id>')
@login_required
def campaign_stats(campaign_id):
    """Statistiques agregees d'une campagne."""
    campaign = Campaign.query.get_or_404(campaign_id)
    if not g.current_user.can_access_campaign(campaign):
        flash('Acces interdit a cette campagne.', 'error')
        return redirect(url_for('main.index'))

    combats = Combat.query.filter_by(campaign_id=campaign.id).order_by(Combat.created_at.desc()).all()
    stats = _build_aggregate_stats(combats)

    return render_template(
        'summary_aggregate.html',
        scope_type='campaign',
        scope_title=campaign.name,
        stats=stats,
        combats=combats,
        export_url=url_for('summary.campaign_stats_export', campaign_id=campaign.id),
    )


@bp.route('/campaign/<int:campaign_id>/export')
@login_required
def campaign_stats_export(campaign_id):
    """Export JSON des statistiques campagne."""
    campaign = Campaign.query.get_or_404(campaign_id)
    if not g.current_user.can_access_campaign(campaign):
        return jsonify({'error': 'forbidden'}), 403

    combats = Combat.query.filter_by(campaign_id=campaign.id).all()
    return jsonify({
        'scope': 'campaign',
        'id': campaign.id,
        'name': campaign.name,
        'stats': _build_aggregate_stats(combats),
    })


@bp.route('/arc/<int:arc_id>')
@login_required
def arc_stats(arc_id):
    """Statistiques agregees d'un arc narratif."""
    arc = StoryArc.query.get_or_404(arc_id)
    if not g.current_user.can_access_campaign(arc.campaign):
        flash('Acces interdit a cet arc.', 'error')
        return redirect(url_for('main.index'))

    combats = Combat.query.filter_by(story_arc_id=arc.id).order_by(Combat.created_at.desc()).all()
    stats = _build_aggregate_stats(combats)

    return render_template(
        'summary_aggregate.html',
        scope_type='arc',
        scope_title=arc.name,
        stats=stats,
        combats=combats,
        export_url=url_for('summary.arc_stats_export', arc_id=arc.id),
    )


@bp.route('/arc/<int:arc_id>/export')
@login_required
def arc_stats_export(arc_id):
    """Export JSON des statistiques arc."""
    arc = StoryArc.query.get_or_404(arc_id)
    if not g.current_user.can_access_campaign(arc.campaign):
        return jsonify({'error': 'forbidden'}), 403

    combats = Combat.query.filter_by(story_arc_id=arc.id).all()
    return jsonify({
        'scope': 'arc',
        'id': arc.id,
        'name': arc.name,
        'campaign_id': arc.campaign_id,
        'stats': _build_aggregate_stats(combats),
    })
