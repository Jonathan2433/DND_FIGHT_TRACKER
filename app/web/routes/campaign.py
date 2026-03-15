# Migrated to app.web.routes
"""Routes pour la gestion des campagnes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from app.application.use_cases.campaign_service import CampaignService
from app.application.use_cases.auth_service import AuthService
from app.application.use_cases.notification_service import NotificationService
from app.utils.decorators import login_required, mj_or_admin_required
from app.models.campaign import Campaign, CampaignMember, CampaignInvitation, JoinRequest
from app.models.combat import Combat
from app.models.user import User
from app.models import CharacterTemplate
from app.extensions import db

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
    campaign_pjs = CharacterTemplate.query.filter(
        CharacterTemplate.character_type == 'PJ',
        CharacterTemplate.is_active.is_(True),
        (
            (CharacterTemplate.campaign_id == campaign_id) |
            CharacterTemplate.campaigns.any(id=campaign_id)
        )
    ).all()

    visible_campaign_pjs = [
        pj for pj in campaign_pjs
        if pj.can_be_viewed_by(g.current_user, campaign)
    ]

    combats_count = Combat.query.filter_by(campaign_id=campaign_id).count()

    visible_campaign_pnjs = [
        pnj for pnj in campaign.characters
        if pnj.character_type == 'PNJ' and pnj.is_active and (g.current_user.is_mj_of(campaign) or pnj.is_shared)
    ]

    current_arc = next((arc for arc in campaign.story_arcs if arc.status == 'en_cours'), None)

    # PJ du joueur courant pouvant être ajoutés à cette campagne
    available_player_pjs = []
    if not g.current_user.is_mj_of(campaign):
        available_player_pjs = CharacterTemplate.query.filter_by(
            owner_id=g.current_user.id,
            character_type='PJ',
            is_active=True
        ).filter(
            ~CharacterTemplate.campaigns.any(id=campaign_id)
        ).order_by(CharacterTemplate.name.asc()).all()

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
        visible_campaign_pjs=visible_campaign_pjs,
        invitations=invitations,
        join_requests=join_requests,
        is_mj=g.current_user.is_mj_of(campaign),
        combats_count=combats_count,
        current_arc=current_arc,
        available_player_pjs=available_player_pjs,
        visible_campaign_pnjs=visible_campaign_pnjs
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


@bp.route('/<int:campaign_id>/add_pj', methods=['POST'])
@login_required
def add_player_character(campaign_id):
    """Associer un PJ du joueur connecté à la campagne."""
    campaign = CampaignService.get_campaign_with_access_check(campaign_id, g.current_user.id)

    if not campaign:
        flash('Campagne non trouvée ou accès interdit.', 'error')
        return redirect(url_for('main.index'))

    if g.current_user.is_mj_of(campaign):
        flash('Cette action est réservée aux joueurs de la campagne.', 'error')
        return redirect(url_for('campaign.view_campaign', campaign_id=campaign_id))

    character_id = request.form.get('character_id', type=int)
    if not character_id:
        flash('Veuillez sélectionner un PJ.', 'error')
        return redirect(url_for('campaign.view_campaign', campaign_id=campaign_id))

    character = CharacterTemplate.query.filter_by(
        id=character_id,
        owner_id=g.current_user.id,
        character_type='PJ',
        is_active=True
    ).first()

    if not character:
        flash('PJ introuvable ou non autorisé.', 'error')
        return redirect(url_for('campaign.view_campaign', campaign_id=campaign_id))

    if campaign not in character.campaigns:
        character.campaigns.append(campaign)
    character.campaign_id = campaign_id
    db.session.commit()

    NotificationService.create_notification(
        campaign.mj_id,
        "Nouveau PJ dans la campagne",
        f'{g.current_user.username} a ajouté son PJ "{character.name}" à la campagne "{campaign.name}".',
        kind='player_pj_added',
        campaign_id=campaign.id,
    )

    flash(f'🎉 {character.name} est maintenant associé à cette campagne !', 'success')
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
        removed_username = member.user.username
        db.session.delete(member)
        db.session.commit()

        NotificationService.create_notification(
            user_id=user_id,
            title="Retrait de campagne",
            message=f'Le MJ vous a retiré de la campagne "{campaign.name}".',
            kind='campaign_member_removed',
            campaign_id=campaign.id,
        )
        flash(f'Membre {removed_username} retiré de la campagne.', 'success')

    return redirect(url_for('campaign.campaign_settings', campaign_id=campaign_id))
