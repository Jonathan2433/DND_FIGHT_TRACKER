"""Routes pour la gestion des episodes."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, g

from app.application.use_cases.campaign_service import CampaignService
from app.application.use_cases.episode_email_service import EpisodeEmailService, EpisodeEmailServiceError
from app.application.use_cases.episode_service import EpisodeService
from app.application.use_cases.episode_summary_service import (
    EpisodeSummaryAccessError,
    EpisodeSummaryAlreadyRunningError,
    EpisodeSummaryGenerationError,
    EpisodeSummaryService,
)
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
    shared_notes = EpisodeService.list_shared_notes(episode.id)

    return render_template(
        'episode/view_episode.html',
        episode=episode,
        arc=arc,
        campaign=campaign,
        my_note=my_note,
        shared_notes=shared_notes,
        is_mj=g.current_user.is_mj_of(campaign),
    )


@bp.route('/<int:episode_id>/edit', methods=['POST'])
@login_required
def update_episode(episode_id):
    """Modifier le titre et le resume partage de l'episode (MJ uniquement)."""
    episode = Episode.query.get_or_404(episode_id)
    campaign = CampaignService.get_campaign_with_access_check(episode.story_arc.campaign_id, g.current_user.id)

    if not campaign or not g.current_user.is_mj_of(campaign):
        flash('Seul le MJ peut modifier cet episode.', 'error')
        return redirect(url_for('episode.view_episode', episode_id=episode_id))

    title = request.form.get('title', '').strip()
    if not title:
        flash("Le titre de l'episode est obligatoire.", 'error')
        return redirect(url_for('episode.view_episode', episode_id=episode_id))

    summary_shared = request.form.get('summary_shared', '').strip()
    EpisodeService.update_episode(episode_id, title, summary_shared)
    flash('Episode mis a jour.', 'success')
    return redirect(url_for('episode.view_episode', episode_id=episode_id))


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
    """Modifier la note partagee de l'utilisateur courant."""
    episode = Episode.query.get_or_404(episode_id)
    campaign = CampaignService.get_campaign_with_access_check(episode.story_arc.campaign_id, g.current_user.id)

    if not campaign:
        flash('Acces interdit a cet episode.', 'error')
        return redirect(url_for('main.index'))

    notes = request.form.get('notes', '').strip()
    EpisodeService.update_user_note(episode_id, g.current_user.id, notes)
    flash('Votre note partagee a ete enregistree.', 'success')
    return redirect(url_for('episode.view_episode', episode_id=episode_id))


@bp.route('/<int:episode_id>/my_private_notes', methods=['POST'])
@login_required
def update_my_private_notes(episode_id):
    """Modifier la note privee de l'utilisateur courant."""
    episode = Episode.query.get_or_404(episode_id)
    campaign = CampaignService.get_campaign_with_access_check(episode.story_arc.campaign_id, g.current_user.id)

    if not campaign:
        flash('Acces interdit a cet episode.', 'error')
        return redirect(url_for('main.index'))

    private_notes = request.form.get('private_notes', '').strip()
    EpisodeService.update_user_private_note(episode_id, g.current_user.id, private_notes)
    flash('Votre note privee a ete enregistree.', 'success')
    return redirect(url_for('episode.view_episode', episode_id=episode_id))


@bp.route('/<int:episode_id>/summary/generate', methods=['POST'])
@login_required
def generate_episode_summary(episode_id):
    """Generer ou regenerer le resume public de l'episode (MJ uniquement)."""
    episode = Episode.query.get_or_404(episode_id)
    campaign = CampaignService.get_campaign_with_access_check(episode.story_arc.campaign_id, g.current_user.id)
    if not campaign:
        flash('Acces interdit a cet episode.', 'error')
        return redirect(url_for('main.index'))

    send_email = (request.form.get('send_email') or '').lower() in {'1', 'true', 'on', 'yes'}
    force_email = (request.form.get('force_email') or '').lower() in {'1', 'true', 'on', 'yes'}
    force_regenerate = (request.form.get('force_regenerate') or '').lower() in {'1', 'true', 'on', 'yes'}

    try:
        source_payload = EpisodeSummaryService.build_public_source_payload(episode)
        source_hash = EpisodeSummaryService.compute_source_hash(source_payload)

        if force_regenerate:
            episode.summary_source_hash = None

        result = EpisodeSummaryService.generate_public_summary_for_episode(
            episode_id=episode_id,
            triggered_by_user_id=g.current_user.id,
            send_email=False,
        )

        if result.get('skipped'):
            flash('Aucun changement detecte: le resume existant est deja a jour.', 'info')
        else:
            flash('Resume d\'episode genere avec succes.', 'success')

        if send_email:
            email_result = EpisodeEmailService.send_episode_summary_email(
                episode=episode,
                source_hash=source_hash,
                summary_text=(result.get('summary') or episode.summary_public or ''),
                force=force_email,
            )
            if email_result.get('sent'):
                flash(f"Resume envoye par email ({email_result.get('recipient_count', 0)} destinataires).", 'success')
            elif email_result.get('skipped'):
                flash('Email non renvoye: ce resume a deja ete diffuse.', 'info')

    except EpisodeSummaryAlreadyRunningError as exc:
        flash(str(exc), 'warning')
    except EpisodeSummaryAccessError as exc:
        flash(str(exc), 'error')
    except EpisodeSummaryGenerationError as exc:
        flash(f'Echec de generation du resume: {exc}', 'error')
    except EpisodeEmailServiceError as exc:
        flash(f'Resume genere, mais envoi email en echec: {exc}', 'warning')

    return redirect(url_for('episode.view_episode', episode_id=episode_id))


@bp.route('/<int:episode_id>/summary/send-email', methods=['POST'])
@login_required
def send_episode_summary_email(episode_id):
    """Envoyer (ou renvoyer) le resume deja genere par email (MJ uniquement)."""
    episode = Episode.query.get_or_404(episode_id)
    campaign = CampaignService.get_campaign_with_access_check(episode.story_arc.campaign_id, g.current_user.id)
    if not campaign:
        flash('Acces interdit a cet episode.', 'error')
        return redirect(url_for('main.index'))

    force_email = (request.form.get('force_email') or '').lower() in {'1', 'true', 'on', 'yes'}

    try:
        EpisodeSummaryService._assert_can_manage_summary(g.current_user, campaign)
        source_payload = EpisodeSummaryService.build_public_source_payload(episode)
        source_hash = EpisodeSummaryService.compute_source_hash(source_payload)
        result = EpisodeEmailService.send_episode_summary_email(
            episode=episode,
            source_hash=source_hash,
            force=force_email,
        )

        if result.get('sent'):
            flash(f"Resume envoye par email ({result.get('recipient_count', 0)} destinataires).", 'success')
        else:
            flash('Email non renvoye: ce resume a deja ete diffuse.', 'info')

    except EpisodeSummaryAccessError as exc:
        flash(str(exc), 'error')
    except EpisodeEmailServiceError as exc:
        flash(f'Echec de l\'envoi email: {exc}', 'error')

    return redirect(url_for('episode.view_episode', episode_id=episode_id))
