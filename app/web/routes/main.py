# Migrated to app.web.routes
"""Routes principales."""
import re
import unicodedata

from flask import Blueprint, abort, render_template, session, g, request, url_for

from app.application.use_cases.campaign_service import CampaignService
from app.models import Combat, CharacterTemplate, Campaign, User
from app.models.story_arc import StoryArc
from app.models.episode import Episode
from app.utils import format_duration
from app.utils.spell_catalog import load_spell_catalog


bp = Blueprint('main', __name__)


def _slugify_spell_name(name):
    normalized = unicodedata.normalize('NFKD', name or '')
    ascii_name = normalized.encode('ascii', 'ignore').decode('ascii')
    lowered = ascii_name.lower()
    cleaned = re.sub(r'[^a-z0-9]+', '-', lowered).strip('-')
    return cleaned or 'sort'


def _build_campaign_summary(campaign):
    arcs = sorted(campaign.story_arcs, key=lambda arc: arc.order_index)
    current_arc = next((arc for arc in arcs if arc.status == 'en_cours'), None)
    if not current_arc:
        current_arc = next((arc for arc in arcs if arc.status == 'à_venir'), None)
    if not current_arc and arcs:
        current_arc = arcs[-1]

    latest_episode = (
        Episode.query.join(StoryArc, Episode.story_arc_id == StoryArc.id)
        .filter(StoryArc.campaign_id == campaign.id)
        .order_by(Episode.created_at.desc(), Episode.order_index.desc())
        .first()
    )

    return {
        'campaign': campaign,
        'current_arc': current_arc,
        'latest_episode': latest_episode,
    }


@bp.route('/')
def index():
    """Page d'accueil."""
    combats = Combat.query.order_by(Combat.created_at.desc()).all()

    total_combats = Combat.query.count()
    total_campaigns = Campaign.query.count()
    total_pj = CharacterTemplate.query.filter_by(character_type='PJ', is_active=True).count()
    total_users = User.query.count()

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
    mj_campaign_summaries = []

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
            featured_campaign_summary = _build_campaign_summary(featured_campaign)

            mj_campaigns = [campaign for campaign in user_campaigns if campaign.mj_id == g.current_user.id]
            mj_campaign_summaries = [
                _build_campaign_summary(campaign)
                for campaign in sorted(mj_campaigns, key=lambda campaign: campaign.created_at, reverse=True)
            ]

    return render_template(
        'index.html',
        total_campaigns=total_campaigns,
        total_combats=total_combats,
        total_pj=total_pj,
        total_users=total_users,
        combat_cards=combat_cards,
        user_is_connected=user_is_connected,
        user_campaigns=user_campaigns,
        user_characters=user_characters,
        featured_campaign_summary=featured_campaign_summary,
        mj_campaign_summaries=mj_campaign_summaries,
    )


@bp.route('/public_campaigns')
def public_campaigns():
    """Lister les campagnes publiques."""
    campaigns = CampaignService.get_public_campaigns()
    return render_template('campaign/public_campaigns.html', public_campaigns=campaigns)


@bp.route('/bibliotheque-des-sorts')
def spell_library():
    """Bibliothèque publique de sorts."""
    spells = sorted(load_spell_catalog(), key=lambda spell: spell.get('name', '').lower())
    for spell in spells:
        spell['slug'] = _slugify_spell_name(spell.get('name', ''))
    return render_template('spell_library.html', spells=spells)


@bp.route('/bibliotheque-des-sorts/<spell_slug>')
def spell_detail(spell_slug):
    """Détail d'un sort avec son contenu complet."""
    spell = next(
        (
            candidate for candidate in load_spell_catalog()
            if _slugify_spell_name(candidate.get('name', '')) == spell_slug
        ),
        None,
    )
    if spell is None:
        abort(404)
    return_to = request.args.get('return_to') or url_for('main.spell_library')
    return_label = request.args.get('return_label') or 'Retour à la bibliothèque'
    return render_template(
        'spell_detail.html',
        spell=spell,
        return_to=return_to,
        return_label=return_label,
    )
