# Migrated to app.web.routes
"""Routes pour la gestion des campagnes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from app.application.use_cases.campaign_service import CampaignService
from app.application.use_cases.auth_service import AuthService
from app.utils.decorators import login_required, mj_or_admin_required
from app.models.campaign import Campaign, CampaignMember, CampaignInvitation, JoinRequest
from app.models.user import User

# Créer le blueprint
bp = Blueprint('campaign', __name__, url_prefix='/campaign')


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_campaign():
    """Créer une nouvelle campagne AVEC gestion public/privé"""
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        is_public = bool(request.form.get('is_public', False))  # ✅ AJOUT

        campaign = CampaignService.create_campaign(name, description, g.current_user.id, is_public)
        flash(f'Campagne "{campaign.name}" créée avec succès !', 'success')
        return redirect(url_for('campaign.view_campaign', campaign_id=campaign.id))

    return render_template('campaign/create_campaign.html')


# app/routes/campaign.py - MODIFIER cette méthode view_campaign

@bp.route('/<int:campaign_id>')
@login_required
def view_campaign(campaign_id):
    """Afficher le tableau de bord d'une campagne"""
    campaign = CampaignService.get_campaign_with_access_check(campaign_id, g.current_user.id)

    if not campaign:
        flash('Campagne non trouvée ou accès interdit.', 'error')
        return redirect(url_for('main.index'))

    # Récupérer les membres
    members = CampaignMember.query.filter_by(campaign_id=campaign_id).all()

    # ✅ NOUVEAU : Récupérer les PJ de la campagne
    from app.models import CharacterTemplate
    campaign_pjs = CharacterTemplate.query.filter_by(
        campaign_id=campaign_id,
        character_type='PJ',
        is_active=True
    ).all()

    # Récupérer les invitations en attente (si MJ)
    invitations = []
    join_requests = []
    if g.current_user.is_mj_of(campaign):
        invitations = CampaignInvitation.query.filter_by(
            campaign_id=campaign_id,
            is_accepted=False,
            is_declined=False
        ).all()

        join_requests = JoinRequest.query.filter_by(
            campaign_id=campaign_id,
            is_pending=True
        ).all()

    return render_template(
        'campaign/dashboard.html',
        campaign=campaign,
        members=members,
        campaign_pjs=campaign_pjs,  # ✅ NOUVEAU
        invitations=invitations,
        join_requests=join_requests,
        is_mj=g.current_user.is_mj_of(campaign)
    )


@bp.route('/<int:campaign_id>/invite', methods=['POST'])
@login_required
def invite_user(campaign_id):
    """Inviter un utilisateur à rejoindre la campagne"""
    campaign = CampaignService.get_campaign_with_access_check(campaign_id, g.current_user.id)

    if not campaign or not g.current_user.is_mj_of(campaign):
        flash('Seul le MJ peut inviter des joueurs.', 'error')
        return redirect(url_for('campaign.view_campaign', campaign_id=campaign_id))

    email_or_username = request.form['email_or_username']
    result = CampaignService.invite_user(campaign_id, email_or_username, g.current_user.id)

    if 'error' in result:
        flash(result['error'], 'error')
    else:
        flash(result['message'], 'success')

    return redirect(url_for('campaign.view_campaign', campaign_id=campaign_id))


@bp.route('/accept/<token>')
@login_required
def accept_invitation(token):
    """Accepter une invitation à rejoindre une campagne"""
    result = CampaignService.accept_invitation(token, g.current_user.id)

    if 'error' in result:
        flash(result['error'], 'error')
        return redirect(url_for('main.index'))

    flash(f'Vous avez rejoint la campagne "{result["campaign"].name}" !', 'success')
    return redirect(url_for('campaign.view_campaign', campaign_id=result["campaign"].id))


@bp.route('/decline/<token>')
@login_required
def decline_invitation(token):
    """Refuser une invitation a rejoindre une campagne."""
    result = CampaignService.decline_invitation(token, g.current_user.id)

    if 'error' in result:
        flash(result['error'], 'error')
    else:
        flash('Invitation refusee.', 'info')

    return redirect(url_for('main.index'))


@bp.route('/<int:campaign_id>/request_join', methods=['POST'])
@login_required
def request_join(campaign_id):
    """Demander à rejoindre une campagne - AVEC VÉRIFICATION PUBLIC/PRIVÉ"""
    message = request.form.get('message', '')
    result = CampaignService.request_to_join(campaign_id, g.current_user.id, message)

    if 'error' in result:
        flash(result['error'], 'error')
    else:
        flash(result['message'], 'success')

    return redirect(url_for('main.index'))


@bp.route('/join_request/<int:request_id>/approve', methods=['POST'])
@login_required
def approve_join_request(request_id):
    """Approuver une demande de rejoindre"""
    result = CampaignService.approve_join_request(request_id, g.current_user.id)

    if 'error' in result:
        flash(result['error'], 'error')
    else:
        flash(result['message'], 'success')

    # Rediriger vers la campagne
    join_request = JoinRequest.query.get(request_id)
    if join_request:
        return redirect(url_for('campaign.view_campaign', campaign_id=join_request.campaign_id))

    return redirect(url_for('main.index'))


@bp.route('/join_request/<int:request_id>/reject', methods=['POST'])
@login_required
def reject_join_request(request_id):
    """Refuser une demande de rejoindre."""
    join_request = JoinRequest.query.get_or_404(request_id)
    campaign_id = join_request.campaign_id

    result = CampaignService.reject_join_request(request_id, g.current_user.id)
    if 'error' in result:
        flash(result['error'], 'error')
    else:
        flash(result['message'], 'success')

    return redirect(url_for('campaign.view_campaign', campaign_id=campaign_id))


@bp.route('/<int:campaign_id>/leave', methods=['POST'])
@login_required
def leave_campaign(campaign_id):
    """Quitter une campagne"""
    result = CampaignService.leave_campaign(campaign_id, g.current_user.id)

    if 'error' in result:
        flash(result['error'], 'error')
    else:
        flash(result['message'], 'success')
        return redirect(url_for('main.index'))

    return redirect(url_for('campaign.view_campaign', campaign_id=campaign_id))


@bp.route('/list')
def list_campaigns():
    """Lister toutes les campagnes - Accessible à tous"""
    from flask import session

    # Si connecté : ses campagnes + campagnes publiques disponibles
    if 'user_id' in session:
        user_campaigns = g.current_user.get_campaigns()

        # Campagnes publiques où il peut demander à rejoindre
        available_campaigns = CampaignService.get_public_campaigns_for_user(g.current_user.id)

        return render_template(
            'campaign/list_campaigns.html',
            user_campaigns=user_campaigns,
            public_campaigns=available_campaigns
        )

    # Si non connecté : seulement campagnes publiques
    else:
        public_campaigns = CampaignService.get_public_campaigns()
        return render_template(
            'campaign/public_campaigns.html',
            public_campaigns=public_campaigns
        )


@bp.route('/<int:campaign_id>/settings')
@login_required
def campaign_settings(campaign_id):
    """Paramètres de la campagne (MJ uniquement)"""
    campaign = CampaignService.get_campaign_with_access_check(campaign_id, g.current_user.id)

    if not campaign or not g.current_user.is_mj_of(campaign):
        flash('Seul le MJ peut modifier les paramètres de la campagne.', 'error')
        return redirect(url_for('campaign.view_campaign', campaign_id=campaign_id))

    members = CampaignMember.query.filter_by(campaign_id=campaign_id).all()

    return render_template(
        'campaign/settings.html',
        campaign=campaign,
        members=members
    )


@bp.route('/<int:campaign_id>/update', methods=['POST'])
@login_required
def update_campaign(campaign_id):
    """Mettre a jour une campagne (MJ proprietaire)."""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    is_public = bool(request.form.get('is_public'))

    result = CampaignService.update_campaign(
        campaign_id=campaign_id,
        user_id=g.current_user.id,
        name=name or None,
        description=description,
        is_public=is_public,
    )

    if 'error' in result:
        flash(result['error'], 'error')
    else:
        flash('Campagne mise a jour avec succes.', 'success')

    return redirect(url_for('campaign.campaign_settings', campaign_id=campaign_id))


@bp.route('/<int:campaign_id>/delete', methods=['POST'])
@login_required
def delete_campaign(campaign_id):
    """Supprimer une campagne (MJ proprietaire)."""
    result = CampaignService.delete_campaign(campaign_id, g.current_user.id)

    if 'error' in result:
        flash(result['error'], 'error')
        return redirect(url_for('campaign.campaign_settings', campaign_id=campaign_id))

    flash('Campagne supprimee.', 'success')
    return redirect(url_for('main.index'))


@bp.route('/<int:campaign_id>/remove_member/<int:user_id>', methods=['POST'])
@login_required
def remove_member(campaign_id, user_id):
    """Retirer un membre de la campagne (MJ uniquement)"""
    campaign = CampaignService.get_campaign_with_access_check(campaign_id, g.current_user.id)

    if not campaign or not g.current_user.is_mj_of(campaign):
        flash('Seul le MJ peut retirer des membres.', 'error')
        return redirect(url_for('campaign.view_campaign', campaign_id=campaign_id))

    member = CampaignMember.query.filter_by(
        campaign_id=campaign_id,
        user_id=user_id
    ).first()

    if member:
        from app.extensions import db
        db.session.delete(member)
        db.session.commit()
        flash('Membre retiré de la campagne.', 'success')

    return redirect(url_for('campaign.campaign_settings', campaign_id=campaign_id))
