# app/services/campaign_service.py - VERSION COMPLÈTE CORRIGÉE

"""Service métier pour la gestion des campagnes"""
from datetime import datetime, timedelta
from flask import url_for
from app.extensions import db
from app.models.campaign import Campaign, CampaignMember, CampaignInvitation, JoinRequest
from app.models.user import User
from app.services.email_service import EmailService


class CampaignService:
    """Service principal pour la gestion des campagnes"""

    @staticmethod
    def create_campaign(name, description, mj_id, is_public=False):
        """Créer une nouvelle campagne AVEC gestion du statut public/privé"""
        campaign = Campaign(
            name=name,
            description=description,
            mj_id=mj_id,
            is_public=is_public  # ✅ AJOUT CRITIQUE
        )

        db.session.add(campaign)
        db.session.commit()

        return campaign

    # ✅ AJOUT : Méthodes pour campagnes publiques
    @staticmethod
    def get_public_campaigns():
        """Récupérer les campagnes publiques pour les non-connectés"""
        return Campaign.query.filter_by(
            is_public=True, 
            is_active=True
        ).order_by(Campaign.created_at.desc()).all()

    @staticmethod
    def get_public_campaigns_for_user(user_id):
        """Campagnes publiques où l'utilisateur peut demander à rejoindre"""
        from app.models.user import User
        
        user = User.query.get_or_404(user_id)
        user_campaign_ids = [c.id for c in user.get_campaigns()]
        
        return Campaign.query.filter(
            Campaign.is_public == True,
            Campaign.is_active == True,
            Campaign.id.notin_(user_campaign_ids)  # Exclure ses campagnes
        ).limit(10).all()

    @staticmethod
    def invite_user(campaign_id, email_or_username, inviter_id):
        """Inviter un utilisateur à rejoindre une campagne"""
        campaign = Campaign.query.get_or_404(campaign_id)

        # Vérifier que l'inviteur est le MJ
        if campaign.mj_id != inviter_id:
            return {"error": "Seul le MJ peut inviter des joueurs"}

        # Chercher l'utilisateur
        user = User.query.filter(
            (User.email == email_or_username) |
            (User.username == email_or_username)
        ).first()

        # Vérifier si déjà membre
        if user and CampaignMember.query.filter_by(campaign_id=campaign_id, user_id=user.id).first():
            return {"error": "Cet utilisateur est déjà membre de la campagne"}

        # Générer token d'invitation
        token = CampaignInvitation.generate_token()
        expires_at = datetime.utcnow() + timedelta(days=7)

        invitation = CampaignInvitation(
            campaign_id=campaign_id,
            invited_user_id=user.id if user else None,
            invited_email=email_or_username if not user else user.email,
            token=token,
            expires_at=expires_at
        )

        db.session.add(invitation)
        db.session.commit()

        # Envoyer email d'invitation
        invitation_url = url_for('campaign.accept_invitation', token=token, _external=True)

        EmailService.send_campaign_invitation(
            invitation.invited_email,
            campaign.name,
            invitation_url,
            user.username if user else email_or_username
        )

        return {"success": True, "message": "Invitation envoyée avec succès"}

    @staticmethod
    def accept_invitation(token, user_id):
        """Accepter une invitation à rejoindre une campagne"""
        invitation = CampaignInvitation.query.filter_by(token=token).first()

        if not invitation:
            return {"error": "Invitation invalide"}

        if invitation.is_accepted:
            return {"error": "Invitation déjà acceptée"}

        if invitation.is_declined:
            return {"error": "Invitation refusée"}

        if datetime.utcnow() > invitation.expires_at:
            return {"error": "Invitation expirée"}

        # Vérifier que l'utilisateur correspond
        if invitation.invited_user_id and invitation.invited_user_id != user_id:
            return {"error": "Cette invitation n'est pas pour vous"}

        # Ajouter comme membre
        member = CampaignMember(
            campaign_id=invitation.campaign_id,
            user_id=user_id
        )

        invitation.is_accepted = True

        db.session.add(member)
        db.session.commit()

        return {"success": True, "campaign": invitation.campaign}

    @staticmethod
    def request_to_join(campaign_id, user_id, message=""):
        """Demander à rejoindre une campagne - AVEC VÉRIFICATION PUBLIC/PRIVÉ"""
        campaign = Campaign.query.get_or_404(campaign_id)
        
        # ✅ AJOUT CRITIQUE : Vérification campagne publique
        if not campaign.is_public:
            return {"error": "Cette campagne est privée. Seul le MJ peut vous inviter."}
        
        # Vérifier si déjà membre
        if CampaignMember.query.filter_by(campaign_id=campaign_id, user_id=user_id).first():
            return {"error": "Vous êtes déjà membre de cette campagne"}

        # Vérifier si demande déjà envoyée
        if JoinRequest.query.filter_by(campaign_id=campaign_id, user_id=user_id, is_pending=True).first():
            return {"error": "Vous avez déjà une demande en attente"}

        request = JoinRequest(
            campaign_id=campaign_id,
            user_id=user_id,
            message=message
        )

        db.session.add(request)
        db.session.commit()

        return {"success": True, "message": "Demande envoyée au MJ"}

    @staticmethod
    def approve_join_request(request_id, approver_id):
        """Approuver une demande de rejoindre"""
        request = JoinRequest.query.get_or_404(request_id)
        campaign = request.campaign

        # Vérifier que l'approbateur est le MJ
        if campaign.mj_id != approver_id:
            return {"error": "Seul le MJ peut approuver les demandes"}

        # Ajouter comme membre
        member = CampaignMember(
            campaign_id=campaign.id,
            user_id=request.user_id
        )

        request.is_pending = False
        request.is_approved = True

        db.session.add(member)
        db.session.commit()

        return {"success": True, "message": "Demande approuvée"}

    @staticmethod
    def get_campaign_with_access_check(campaign_id, user_id):
        """Récupérer une campagne en vérifiant l'accès"""
        campaign = Campaign.query.get_or_404(campaign_id)
        user = User.query.get_or_404(user_id)

        if not user.can_access_campaign(campaign):
            return None

        return campaign

    @staticmethod
    def leave_campaign(campaign_id, user_id):
        """Quitter une campagne"""
        campaign = Campaign.query.get_or_404(campaign_id)

        # Le MJ ne peut pas quitter sa propre campagne
        if campaign.mj_id == user_id:
            return {"error": "Le MJ ne peut pas quitter sa propre campagne"}

        member = CampaignMember.query.filter_by(
            campaign_id=campaign_id,
            user_id=user_id
        ).first()

        if not member:
            return {"error": "Vous n'êtes pas membre de cette campagne"}

        db.session.delete(member)
        db.session.commit()

        return {"success": True, "message": "Vous avez quitté la campagne"}

    @staticmethod
    def get_campaign_pjs(campaign_id):
        """Récupérer tous les PJ d'une campagne"""
        from app.models import CharacterTemplate
        return CharacterTemplate.query.filter_by(
            campaign_id=campaign_id,
            character_type='PJ',
            is_active=True
        ).all()