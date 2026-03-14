# Migrated to app.web.routes
"""Routes pour la gestion des arcs narratifs"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.application.use_cases.story_arc_service import StoryArcService
from app.application.use_cases.campaign_service import CampaignService
from app.application.use_cases.notification_service import NotificationService
from app.utils.decorators import login_required
from app.models.story_arc import StoryArc
from flask import g

# Créer le blueprint
bp = Blueprint('story_arc', __name__, url_prefix='/story_arc')


@bp.route('/campaign/<int:campaign_id>/create', methods=['GET', 'POST'])
@login_required
def create_arc(campaign_id):
    """Créer un nouvel arc narratif"""
    campaign = CampaignService.get_campaign_with_access_check(campaign_id, g.current_user.id)

    if not campaign or not g.current_user.is_mj_of(campaign):
        flash('Seul le MJ peut créer des arcs narratifs.', 'error')
        return redirect(url_for('campaign.view_campaign', campaign_id=campaign_id))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        estimated_sessions = int(request.form.get('estimated_sessions', 1))

        arc = StoryArcService.create_story_arc(campaign_id, name, description, estimated_sessions)

        NotificationService.create_campaign_notification(
            campaign,
            "Nouvel arc narratif",
            f'Le MJ a créé un nouvel arc : "{arc.name}" dans la campagne "{campaign.name}".',
            kind='story_arc_created',
        )

        flash(f'Arc narratif "{arc.name}" créé avec succès !', 'success')
        return redirect(url_for('campaign.view_campaign', campaign_id=campaign_id))

    return render_template('story_arc/create_arc.html', campaign=campaign)


@bp.route('/<int:arc_id>')
@login_required
def view_arc(arc_id):
    """Afficher les détails d'un arc narratif"""
    arc = StoryArc.query.get_or_404(arc_id)

    # Vérifier l'accès à la campagne
    campaign = CampaignService.get_campaign_with_access_check(arc.campaign_id, g.current_user.id)
    if not campaign:
        flash('Accès interdit à cette campagne.', 'error')
        return redirect(url_for('main.index'))

    stats = StoryArcService.get_arc_statistics(arc_id)

    return render_template('story_arc/view_arc.html',
                           arc=arc,
                           campaign=campaign,
                           stats=stats,
                           is_mj=g.current_user.is_mj_of(campaign))


@bp.route('/<int:arc_id>/start', methods=['POST'])
@login_required
def start_arc(arc_id):
    """Démarrer un arc narratif"""
    arc = StoryArc.query.get_or_404(arc_id)
    campaign = CampaignService.get_campaign_with_access_check(arc.campaign_id, g.current_user.id)

    if not campaign or not g.current_user.is_mj_of(campaign):
        flash('Seul le MJ peut démarrer des arcs narratifs.', 'error')
        return redirect(url_for('campaign.view_campaign', campaign_id=arc.campaign_id))

    result = StoryArcService.start_story_arc(arc_id)

    if 'error' in result:
        flash(result['error'], 'error')
    else:
        flash(f'Arc "{arc.name}" démarré !', 'success')

    return redirect(url_for('campaign.view_campaign', campaign_id=arc.campaign_id))


@bp.route('/<int:arc_id>/complete', methods=['POST'])
@login_required
def complete_arc(arc_id):
    """Terminer un arc narratif"""
    arc = StoryArc.query.get_or_404(arc_id)
    campaign = CampaignService.get_campaign_with_access_check(arc.campaign_id, g.current_user.id)

    if not campaign or not g.current_user.is_mj_of(campaign):
        flash('Seul le MJ peut terminer des arcs narratifs.', 'error')
        return redirect(url_for('campaign.view_campaign', campaign_id=arc.campaign_id))

    result = StoryArcService.complete_story_arc(arc_id)

    if 'error' in result:
        flash(result['error'], 'error')
    else:
        flash(f'Arc "{arc.name}" terminé !', 'success')

    return redirect(url_for('campaign.view_campaign', campaign_id=arc.campaign_id))


@bp.route('/<int:arc_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_arc(arc_id):
    """Modifier un arc narratif"""
    arc = StoryArc.query.get_or_404(arc_id)
    campaign = CampaignService.get_campaign_with_access_check(arc.campaign_id, g.current_user.id)

    if not campaign or not g.current_user.is_mj_of(campaign):
        flash('Seul le MJ peut modifier des arcs narratifs.', 'error')
        return redirect(url_for('campaign.view_campaign', campaign_id=arc.campaign_id))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        estimated_sessions = int(request.form.get('estimated_sessions', 1))
        notes = request.form.get('notes', '')

        StoryArcService.update_story_arc(arc_id, name, description, estimated_sessions, notes)
        flash('Arc narratif modifié avec succès !', 'success')
        return redirect(url_for('story_arc.view_arc', arc_id=arc_id))

    return render_template('story_arc/edit_arc.html', arc=arc, campaign=campaign)


@bp.route('/<int:arc_id>/delete', methods=['POST'])
@login_required
def delete_arc(arc_id):
    """Supprimer un arc narratif"""
    arc = StoryArc.query.get_or_404(arc_id)
    campaign = CampaignService.get_campaign_with_access_check(arc.campaign_id, g.current_user.id)

    if not campaign or not g.current_user.is_mj_of(campaign):
        flash('Seul le MJ peut supprimer des arcs narratifs.', 'error')
        return redirect(url_for('campaign.view_campaign', campaign_id=arc.campaign_id))

    result = StoryArcService.delete_story_arc(arc_id)

    if 'error' in result:
        flash(result['error'], 'error')
    else:
        flash('Arc narratif supprimé.', 'success')

    return redirect(url_for('campaign.view_campaign', campaign_id=arc.campaign_id))