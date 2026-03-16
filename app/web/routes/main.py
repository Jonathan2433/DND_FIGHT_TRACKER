# Migrated to app.web.routes
"""Routes principales."""
from flask import Blueprint, render_template, session, g

from app.application.use_cases.campaign_service import CampaignService
from app.models import Combat, CharacterTemplate, Campaign
from app.models.story_arc import StoryArc
from app.models.episode import Episode
from app.utils import format_duration


bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Page d'accueil."""
    combats = Combat.query.order_by(Combat.created_at.desc()).all()

    total_combats = Combat.query.count()
    total_campaigns = Campaign.query.count()
    total_pj = CharacterTemplate.query.filter_by(character_type='PJ', is_active=True).count()

    combat_cards = []
    for combat in combats:
        duration = None
        if combat.start_time and combat.end_time:
            total_seconds = (combat.end_time - combat.start_time).total_seconds()
            duration = format_duration(total_seconds)

        combat_cards.append({
            "id": combat.id,
            "name": combat.name,
            "rounds": combat.round,
            "is_closed": combat.is_closed,
            "duration": duration,
            "deaths": len([c for c in combat.combatants if c.is_dead]),
        })

    user_is_connected = 'user_id' in session and g.get('current_user') is not None
    user_campaigns = []
    user_characters = []
    featured_campaign_summary = None

    if user_is_connected:
        user_campaigns = g.current_user.get_campaigns()
        user_characters = (
            CharacterTemplate.query.filter_by(owner_id=g.current_user.id, is_active=True)
            .order_by(CharacterTemplate.created_at.desc())
            .limit(8)
            .all()
        )

        if user_campaigns:
            featured_campaign = sorted(
                user_campaigns,
                key=lambda campaign: campaign.created_at,
                reverse=True,
            )[0]

            arcs = sorted(featured_campaign.story_arcs, key=lambda arc: arc.order_index)
            current_arc = next((arc for arc in arcs if arc.status == 'en_cours'), None)
            if not current_arc:
                current_arc = next((arc for arc in arcs if arc.status == 'à_venir'), None)
            if not current_arc and arcs:
                current_arc = arcs[-1]

            latest_episode = (
                Episode.query.join(StoryArc, Episode.story_arc_id == StoryArc.id)
                .filter(StoryArc.campaign_id == featured_campaign.id)
                .order_by(Episode.created_at.desc(), Episode.order_index.desc())
                .first()
            )

            featured_campaign_summary = {
                'campaign': featured_campaign,
                'current_arc': current_arc,
                'latest_episode': latest_episode,
            }

    return render_template(
        'index.html',
        total_campaigns=total_campaigns,
        total_combats=total_combats,
        total_pj=total_pj,
        combat_cards=combat_cards,
        user_is_connected=user_is_connected,
        user_campaigns=user_campaigns,
        user_characters=user_characters,
        featured_campaign_summary=featured_campaign_summary,
    )


@bp.route('/public_campaigns')
def public_campaigns():
    """Lister les campagnes publiques."""
    campaigns = CampaignService.get_public_campaigns()
    return render_template('campaign/public_campaigns.html', public_campaigns=campaigns)
