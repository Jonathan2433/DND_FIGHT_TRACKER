"""Routes principales - Version finale avec vrais templates"""
from flask import Blueprint, render_template
from app.models import Combat, CharacterTemplate, CombatLog
from app.utils import format_duration

# Créer le blueprint
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Page d'accueil avec statistiques complètes"""
    combats = Combat.query.order_by(Combat.created_at.desc()).all()
    characters = CharacterTemplate.query.order_by(CharacterTemplate.name).all()

    total_combats = Combat.query.count()
    total_closed = Combat.query.filter_by(is_closed=True).count()
    total_pj = CharacterTemplate.query.count()

    # Total des rounds joués (uniquement combats terminés)
    total_rounds = sum(c.round for c in combats if c.is_closed)

    # Stats bonus intéressantes
    total_damage = sum(
        log.value or 0
        for log in CombatLog.query.filter_by(action_type="damage").all()
    )

    total_heal = sum(
        log.value or 0
        for log in CombatLog.query.filter_by(action_type="heal").all()
    )

    combat_cards = []

    for combat in combats:
        # Durée formatée
        if combat.start_time and combat.end_time:
            total_seconds = (combat.end_time - combat.start_time).total_seconds()
            duration = format_duration(total_seconds)
        else:
            duration = None

        # Morts
        total_deaths = len([c for c in combat.combatants if c.is_dead])

        combat_cards.append({
            "id": combat.id,
            "name": combat.name,
            "rounds": combat.round,
            "is_closed": combat.is_closed,
            "duration": duration,
            "deaths": total_deaths
        })

    # ✅ ENFIN : Utiliser le vrai template index.html
    return render_template(
        'index.html',
        combats=combats,
        total_combats=total_combats,
        total_closed=total_closed,
        total_pj=total_pj,
        total_rounds=total_rounds,
        total_damage=total_damage,
        total_heal=total_heal,
        characters=characters,
        combat_cards=combat_cards
    )