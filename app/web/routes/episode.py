"""Routes pour la gestion des episodes."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, g

from app.application.use_cases.campaign_service import CampaignService
from app.application.use_cases.episode_service import EpisodeService
from app.models.episode import Episode
from app.utils.decorators import login_required


bp = Blueprint('episode', __name__, url_prefix='/episode')


@bp.route('/arc/<int:arc_id>/create', methods=['POST'])
@login_required
def create_episode(arc_id):
    """Creer un episode (MJ uniquement)."""
    from app.models.story_arc import StoryArc

    arc = StoryArc.query.get_or_404(arc_id)
    campaign = CampaignService.get_campaign_with_access_check(arc.campaign_id, g.current_user.id)

    if not campaign or not g.current_user.is_mj_of(campaign):
        flash('Seul le MJ peut creer un episode.', 'error')
        return redirect(url_for('story_arc.view_arc', arc_id=arc_id))

    title = request.form.get('title', '').strip()
    summary_shared = request.form.get('summary_shared', '').strip()
    if not title:
        flash('Le titre de l\'episode est obligatoire.', 'error')
        return redirect(url_for('story_arc.view_arc', arc_id=arc_id))

    episode = EpisodeService.create_episode(arc.id, title, summary_shared)
    flash(f'Episode "{episode.title}" cree avec succes.', 'success')
    return redirect(url_for('episode.view_episode', episode_id=episode.id))


@bp.route('/<int:episode_id>')
@login_required
def view_episode(episode_id):
    """Afficher un episode et ses notes."""
    episode = Episode.query.get_or_404(episode_id)
    arc = episode.story_arc
    campaign = CampaignService.get_campaign_with_access_check(arc.campaign_id, g.current_user.id)

    if not campaign:
        flash('Acces interdit a cet episode.', 'error')
        return redirect(url_for('main.index'))

    my_note = EpisodeService.get_or_create_user_note(episode.id, g.current_user.id)

    return render_template(
        'episode/view_episode.html',
        episode=episode,
        arc=arc,
        campaign=campaign,
        my_note=my_note,
        is_mj=g.current_user.is_mj_of(campaign),
    )


@bp.route('/<int:episode_id>/shared_summary', methods=['POST'])
@login_required
def update_shared_summary(episode_id):
    """Modifier le resume partage de l'episode (MJ uniquement)."""
    episode = Episode.query.get_or_404(episode_id)
    campaign = CampaignService.get_campaign_with_access_check(episode.story_arc.campaign_id, g.current_user.id)

    if not campaign or not g.current_user.is_mj_of(campaign):
        flash('Seul le MJ peut modifier le resume partage.', 'error')
        return redirect(url_for('episode.view_episode', episode_id=episode_id))

    summary_shared = request.form.get('summary_shared', '').strip()
    EpisodeService.update_shared_summary(episode_id, summary_shared)
    flash('Resume partage mis a jour.', 'success')
    return redirect(url_for('episode.view_episode', episode_id=episode_id))


@bp.route('/<int:episode_id>/my_notes', methods=['POST'])
@login_required
def update_my_notes(episode_id):
    """Modifier les notes personnelles de l'utilisateur courant."""
    episode = Episode.query.get_or_404(episode_id)
    campaign = CampaignService.get_campaign_with_access_check(episode.story_arc.campaign_id, g.current_user.id)

    if not campaign:
        flash('Acces interdit a cet episode.', 'error')
        return redirect(url_for('main.index'))

    notes = request.form.get('notes', '').strip()
    EpisodeService.update_user_note(episode_id, g.current_user.id, notes)
    flash('Vos notes personnelles ont ete enregistrees.', 'success')
    return redirect(url_for('episode.view_episode', episode_id=episode_id))
