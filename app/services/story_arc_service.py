"""Service métier pour la gestion des arcs narratifs"""
from datetime import datetime
from app.extensions import db
from app.models.story_arc import StoryArc
from app.models.campaign import Campaign


class StoryArcService:
    """Service principal pour la gestion des arcs narratifs"""

    @staticmethod
    def create_story_arc(campaign_id, name, description="", estimated_sessions=1):
        """Créer un nouvel arc narratif"""
        campaign = Campaign.query.get_or_404(campaign_id)

        # Calculer l'index d'ordre (dernier + 1)
        last_arc = StoryArc.query.filter_by(campaign_id=campaign_id).order_by(StoryArc.order_index.desc()).first()
        order_index = (last_arc.order_index + 1) if last_arc else 0

        story_arc = StoryArc(
            campaign_id=campaign_id,
            name=name,
            description=description,
            estimated_sessions=estimated_sessions,
            order_index=order_index
        )

        db.session.add(story_arc)
        db.session.commit()

        return story_arc

    @staticmethod
    def start_story_arc(arc_id):
        """Démarrer un arc narratif"""
        arc = StoryArc.query.get_or_404(arc_id)

        if arc.status != 'à_venir':
            return {"error": "Cet arc ne peut pas être démarré"}

        # Terminer l'arc précédent s'il y en a un
        current_arc = StoryArc.query.filter_by(
            campaign_id=arc.campaign_id,
            status='en_cours'
        ).first()

        if current_arc:
            current_arc.status = 'terminé'
            current_arc.completed_at = datetime.utcnow()

        # Démarrer le nouvel arc
        arc.status = 'en_cours'
        arc.started_at = datetime.utcnow()

        db.session.commit()

        return {"success": True, "arc": arc}

    @staticmethod
    def complete_story_arc(arc_id):
        """Terminer un arc narratif"""
        arc = StoryArc.query.get_or_404(arc_id)

        if arc.status != 'en_cours':
            return {"error": "Cet arc n'est pas en cours"}

        arc.status = 'terminé'
        arc.completed_at = datetime.utcnow()

        db.session.commit()

        return {"success": True, "arc": arc}

    @staticmethod
    def get_campaign_arcs(campaign_id):
        """Récupérer tous les arcs d'une campagne"""
        return StoryArc.query.filter_by(campaign_id=campaign_id).order_by(StoryArc.order_index).all()

    @staticmethod
    def get_current_arc(campaign_id):
        """Récupérer l'arc en cours d'une campagne"""
        return StoryArc.query.filter_by(campaign_id=campaign_id, status='en_cours').first()

    @staticmethod
    def reorder_arcs(campaign_id, arc_orders):
        """Réorganiser l'ordre des arcs"""
        for arc_id, new_order in arc_orders.items():
            arc = StoryArc.query.filter_by(id=arc_id, campaign_id=campaign_id).first()
            if arc:
                arc.order_index = new_order

        db.session.commit()
        return {"success": True}

    @staticmethod
    def update_story_arc(arc_id, name=None, description=None, estimated_sessions=None, notes=None):
        """Mettre à jour un arc narratif"""
        arc = StoryArc.query.get_or_404(arc_id)

        if name:
            arc.name = name
        if description is not None:
            arc.description = description
        if estimated_sessions:
            arc.estimated_sessions = estimated_sessions
        if notes is not None:
            arc.notes = notes

        db.session.commit()

        return arc

    @staticmethod
    def delete_story_arc(arc_id):
        """Supprimer un arc narratif"""
        arc = StoryArc.query.get_or_404(arc_id)

        # Vérifier qu'il n'y a pas de combats liés
        if arc.combats:
            return {"error": "Impossible de supprimer un arc qui contient des combats"}

        # Réorganiser les index des arcs suivants
        following_arcs = StoryArc.query.filter(
            StoryArc.campaign_id == arc.campaign_id,
            StoryArc.order_index > arc.order_index
        ).all()

        for following_arc in following_arcs:
            following_arc.order_index -= 1

        db.session.delete(arc)
        db.session.commit()

        return {"success": True}

    @staticmethod
    def get_arc_statistics(arc_id):
        """Récupérer les statistiques d'un arc"""
        arc = StoryArc.query.get_or_404(arc_id)

        total_combats = len(arc.combats)
        completed_combats = len([c for c in arc.combats if c.is_closed])

        if arc.completed_at and arc.started_at:
            duration_days = (arc.completed_at - arc.started_at).days
        elif arc.started_at:
            duration_days = (datetime.utcnow() - arc.started_at).days
        else:
            duration_days = 0

        return {
            "arc": arc,
            "total_combats": total_combats,
            "completed_combats": completed_combats,
            "duration_days": duration_days,
            "estimated_sessions": arc.estimated_sessions
        }