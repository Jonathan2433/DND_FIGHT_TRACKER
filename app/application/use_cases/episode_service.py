"""Service metier pour la gestion des episodes."""
from app.extensions import db
from app.models.episode import Episode, EpisodeUserNote
from app.models.story_arc import StoryArc


class EpisodeService:
    """Operations de gestion des episodes."""

    @staticmethod
    def create_episode(story_arc_id, title, summary_shared=''):
        """Creer un episode sur un arc."""
        StoryArc.query.get_or_404(story_arc_id)

        last_episode = Episode.query.filter_by(story_arc_id=story_arc_id).order_by(Episode.order_index.desc()).first()
        order_index = (last_episode.order_index + 1) if last_episode else 0

        episode = Episode(
            story_arc_id=story_arc_id,
            title=title,
            summary_shared=summary_shared,
            order_index=order_index,
        )
        db.session.add(episode)
        db.session.commit()
        return episode

    @staticmethod
    def list_arc_episodes(story_arc_id):
        """Lister les episodes d'un arc."""
        return Episode.query.filter_by(story_arc_id=story_arc_id).order_by(Episode.order_index.asc()).all()

    @staticmethod
    def update_shared_summary(episode_id, summary_shared):
        """Mettre a jour le resume partage de l'episode."""
        episode = Episode.query.get_or_404(episode_id)
        episode.summary_shared = summary_shared
        db.session.commit()
        return episode

    @staticmethod
    def update_episode(episode_id, title, summary_shared):
        """Mettre a jour les informations principales d'un episode."""
        episode = Episode.query.get_or_404(episode_id)
        episode.title = title
        episode.summary_shared = summary_shared
        db.session.commit()
        return episode

    @staticmethod
    def get_or_create_user_note(episode_id, user_id):
        """Recuperer ou creer la note perso d'un utilisateur."""
        note = EpisodeUserNote.query.filter_by(episode_id=episode_id, user_id=user_id).first()
        if note:
            return note

        note = EpisodeUserNote(episode_id=episode_id, user_id=user_id, notes='', private_notes='')
        db.session.add(note)
        db.session.commit()
        return note

    @staticmethod
    def update_user_note(episode_id, user_id, notes):
        """Mettre a jour la note partagee d'un utilisateur pour un episode."""
        note = EpisodeUserNote.query.filter_by(episode_id=episode_id, user_id=user_id).first()
        if not note:
            note = EpisodeUserNote(episode_id=episode_id, user_id=user_id)
            db.session.add(note)

        note.notes = notes
        db.session.commit()
        return note

    @staticmethod
    def update_user_private_note(episode_id, user_id, private_notes):
        """Mettre a jour la note privee d'un utilisateur pour un episode."""
        note = EpisodeUserNote.query.filter_by(episode_id=episode_id, user_id=user_id).first()
        if not note:
            note = EpisodeUserNote(episode_id=episode_id, user_id=user_id)
            db.session.add(note)

        note.private_notes = private_notes
        db.session.commit()
        return note

    @staticmethod
    def list_shared_notes(episode_id):
        """Lister les notes d'episode renseignees par les participants."""
        return (
            EpisodeUserNote.query
            .filter(
                EpisodeUserNote.episode_id == episode_id,
                EpisodeUserNote.notes.isnot(None),
                EpisodeUserNote.notes != '',
            )
            .order_by(EpisodeUserNote.updated_at.desc())
            .all()
        )
