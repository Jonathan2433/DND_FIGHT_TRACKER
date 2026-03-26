"""Application use cases (migrated from legacy services)."""

# app/services/campaign_service.py - VERSION COMPLÈTE CORRIGÉE

"""Service métier pour la gestion des campagnes"""
from datetime import datetime, timedelta
from flask import url_for
from app.extensions import db
from sqlalchemy.exc import SQLAlchemyError

from app.models.campaign import Campaign, CampaignMember, CampaignInvitation, JoinRequest
from app.models.user import User
from app.application.use_cases.email_service import EmailService
from app.application.use_cases.notification_service import NotificationService


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

        normalized_input = email_or_username.strip()

        # Chercher l'utilisateur
        user = User.query.filter(
            (User.email == normalized_input) |
            (User.username == normalized_input)
        ).first()

        # Vérifier si déjà membre
        if user and CampaignMember.query.filter_by(campaign_id=campaign_id, user_id=user.id).first():
            return {"error": "Cet utilisateur est déjà membre de la campagne"}

        if not user and '@' not in normalized_input:
            return {"error": "Utilisateur introuvable. Utilisez une adresse email valide pour inviter un nouveau joueur"}

        # Générer token d'invitation
        token = CampaignInvitation.generate_token()
        expires_at = datetime.utcnow() + timedelta(days=7)

        invitation = CampaignInvitation(
            campaign_id=campaign_id,
            invited_user_id=user.id if user else None,
            invited_email=normalized_input if not user else user.email,
            token=token,
            expires_at=expires_at
        )

        db.session.add(invitation)
        db.session.commit()

        if user:
            NotificationService.create_notification(
                user.id,
                "Invitation de campagne",
                f'Le MJ vous a invité à rejoindre la campagne "{campaign.name}".',
                kind='campaign_invitation',
                campaign_id=campaign.id,
            )

        # Envoyer email d'invitation (inscription si compte inexistant)
        if user:
            invitation_url = url_for('campaign.accept_invitation', token=token, _external=True)
            EmailService.send_campaign_invitation(
                invitation.invited_email,
                campaign.name,
                invitation_url,
                user.username,
            )
        else:
            signup_url = url_for(
                'auth.register',
                invitation_token=token,
                invited_email=invitation.invited_email,
                _external=True,
            )
            EmailService.send_campaign_signup_invitation(
                invitation.invited_email,
                campaign.name,
                signup_url,
            )

        return {"success": True, "message": "Invitation envoyée avec succès"}

    @staticmethod
    def get_pending_invitation_for_user(campaign_id, user_id):
        """Retourner l'invitation en attente d'un utilisateur pour une campagne."""
        user = User.query.get_or_404(user_id)

        invitation = CampaignInvitation.query.filter_by(
            campaign_id=campaign_id,
            invited_user_id=user_id,
            is_accepted=False,
            is_declined=False,
        ).order_by(CampaignInvitation.created_at.desc()).first()

        if invitation:
            return invitation

        return CampaignInvitation.query.filter_by(
            campaign_id=campaign_id,
            invited_email=user.email,
            is_accepted=False,
            is_declined=False,
        ).order_by(CampaignInvitation.created_at.desc()).first()

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

        if not invitation.invited_user_id and invitation.invited_email:
            user = User.query.get_or_404(user_id)
            if user.email.lower() != invitation.invited_email.lower():
                return {"error": "Cette invitation est liee a un autre email"}

        # Ajouter comme membre
        member = CampaignMember(
            campaign_id=invitation.campaign_id,
            user_id=user_id
        )

        invitation.is_accepted = True

        db.session.add(member)
        db.session.commit()

        NotificationService.create_notification(
            invitation.campaign.mj_id,
            "Invitation acceptée",
            f"Un joueur a accepté l'invitation pour la campagne \"{invitation.campaign.name}\".",
            kind='campaign_invitation_accepted',
            campaign_id=invitation.campaign_id,
        )

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

        NotificationService.create_notification(
            campaign.mj_id,
            "Demande de rejoindre",
            f'{request.user.username} a demandé à rejoindre la campagne "{campaign.name}".',
            kind='join_request',
            campaign_id=campaign.id,
        )

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

        NotificationService.create_notification(
            request.user_id,
            "Demande acceptée",
            f'Le MJ a accepté votre demande pour rejoindre la campagne "{campaign.name}".',
            kind='join_request_approved',
            campaign_id=campaign.id,
        )

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

        user = User.query.get_or_404(user_id)
        NotificationService.create_notification(
            campaign.mj_id,
            "Départ d'un joueur",
            f'{user.username} a quitté la campagne "{campaign.name}".',
            kind='campaign_member_left',
            campaign_id=campaign.id,
        )

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

    @staticmethod
    def update_campaign(campaign_id, user_id, name=None, description=None, is_public=None):
        """Mettre a jour une campagne (MJ proprietaire uniquement)."""
        campaign = Campaign.query.get_or_404(campaign_id)

        if campaign.mj_id != user_id:
            return {"error": "Seul le MJ proprietaire peut modifier cette campagne"}

        if name is not None:
            campaign.name = name
        if description is not None:
            campaign.description = description
        if is_public is not None:
            campaign.is_public = bool(is_public)

        db.session.commit()
        return {"success": True, "campaign": campaign}

    @staticmethod
    def delete_campaign(campaign_id, user_id):
        """Supprimer une campagne (MJ proprietaire uniquement)."""
        from app.models import (
            CampaignInspirationLog,
            CharacterTemplate,
            Combat,
            CombatLog,
            Episode,
            EpisodeUserNote,
            Notification,
            StoryArc,
            XPLog,
        )
        from app.models.character import character_campaign_association

        campaign = Campaign.query.get_or_404(campaign_id)

        if campaign.mj_id != user_id:
            return {"error": "Seul le MJ proprietaire peut supprimer cette campagne"}

        member_ids = [m.user_id for m in campaign.members]

        try:
            # Notifications "campagne fermée" sans FK sur campagne (la campagne va être supprimée).
            for member_id in member_ids:
                NotificationService.create_notification(
                    member_id,
                    "Campagne fermée",
                    f'Le MJ a fermé la campagne "{campaign.name}".',
                    kind='campaign_closed',
                    campaign_id=None,
                    auto_commit=False,
                )

            # Rompre les liens FK optionnels vers la campagne avant suppression.
            Notification.query.filter_by(campaign_id=campaign.id).update(
                {"campaign_id": None},
                synchronize_session=False,
            )
            CharacterTemplate.query.filter_by(campaign_id=campaign.id).update(
                {"campaign_id": None},
                synchronize_session=False,
            )

            # Supprimer les dépendances non-cascadées de la campagne.
            story_arc_ids_subquery = db.session.query(StoryArc.id).filter_by(campaign_id=campaign.id)
            episode_ids_subquery = db.session.query(Episode.id).filter(Episode.story_arc_id.in_(story_arc_ids_subquery))
            combat_ids_subquery = db.session.query(Combat.id).filter_by(campaign_id=campaign.id)

            EpisodeUserNote.query.filter(EpisodeUserNote.episode_id.in_(episode_ids_subquery)).delete(synchronize_session=False)
            CampaignInspirationLog.query.filter_by(campaign_id=campaign.id).delete(synchronize_session=False)
            XPLog.query.filter(XPLog.combat_id.in_(combat_ids_subquery)).delete(synchronize_session=False)
            CombatLog.query.filter(CombatLog.combat_id.in_(combat_ids_subquery)).delete(synchronize_session=False)
            db.session.execute(
                character_campaign_association.delete().where(
                    character_campaign_association.c.campaign_id == campaign.id
                )
            )
            Combat.query.filter_by(campaign_id=campaign.id).delete(synchronize_session=False)
            Episode.query.filter(Episode.story_arc_id.in_(story_arc_ids_subquery)).delete(synchronize_session=False)
            StoryArc.query.filter_by(campaign_id=campaign.id).delete(synchronize_session=False)
            CampaignInvitation.query.filter_by(campaign_id=campaign.id).delete(synchronize_session=False)
            JoinRequest.query.filter_by(campaign_id=campaign.id).delete(synchronize_session=False)
            CampaignMember.query.filter_by(campaign_id=campaign.id).delete(synchronize_session=False)

            db.session.delete(campaign)
            db.session.commit()
            return {"success": True}
        except SQLAlchemyError:
            db.session.rollback()
            return {
                "error": "Impossible de supprimer cette campagne pour le moment. Réessayez dans quelques instants."
            }


    @staticmethod
    def decline_invitation(token, user_id):
        """Refuser une invitation a rejoindre une campagne."""
        invitation = CampaignInvitation.query.filter_by(token=token).first()

        if not invitation:
            return {"error": "Invitation invalide"}

        if invitation.is_accepted:
            return {"error": "Invitation deja acceptee"}

        if invitation.is_declined:
            return {"error": "Invitation deja refusee"}

        if invitation.invited_user_id and invitation.invited_user_id != user_id:
            return {"error": "Cette invitation n'est pas pour vous"}

        invitation.is_declined = True
        db.session.commit()

        NotificationService.create_notification(
            invitation.campaign.mj_id,
            "Invitation refusée",
            f"Un joueur a refusé l'invitation pour la campagne \"{invitation.campaign.name}\".",
            kind='campaign_invitation_declined',
            campaign_id=invitation.campaign_id,
        )
        return {"success": True}

    @staticmethod
    def reject_join_request(request_id, approver_id):
        """Refuser une demande de rejoindre une campagne."""
        join_request = JoinRequest.query.get_or_404(request_id)
        campaign = join_request.campaign

        if campaign.mj_id != approver_id:
            return {"error": "Seul le MJ peut refuser les demandes"}

        join_request.is_pending = False
        join_request.is_rejected = True
        db.session.commit()

        NotificationService.create_notification(
            join_request.user_id,
            "Demande refusée",
            f'Le MJ a refusé votre demande pour la campagne "{campaign.name}".',
            kind='join_request_rejected',
            campaign_id=campaign.id,
        )
        return {"success": True, "message": "Demande refusee"}
