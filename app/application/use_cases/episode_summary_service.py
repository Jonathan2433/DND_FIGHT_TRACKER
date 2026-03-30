"""Service metier pour la generation de resumes d'episode via LLM."""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
import threading
from typing import Any

from flask import current_app

from app.application.use_cases.episode_email_service import EpisodeEmailService, EpisodeEmailServiceError
from app.application.use_cases.notification_service import NotificationService
from app.application.use_cases.ollama_service import OllamaService
from app.extensions import db
from app.models.combat import Combat, CombatLog
from app.models.episode import Episode, EpisodeUserNote
from app.models.user import User


class EpisodeSummaryError(RuntimeError):
    """Erreur de base du service de resume d'episode."""


class EpisodeSummaryAccessError(EpisodeSummaryError):
    """Erreur d'autorisation pour la generation du resume."""


class EpisodeSummaryAlreadyRunningError(EpisodeSummaryError):
    """Un resume est deja en cours de generation."""


class EpisodeSummaryGenerationError(EpisodeSummaryError):
    """Erreur lors de l'appel LLM ou de la validation du resume."""


class EpisodeSummaryService:
    """Orchestration de la collecte de donnees et de la generation de resume public."""

    SYSTEM_PROMPT = (
        "Tu es l'assistant narratif d'Exalquest.\n\n"
        "Ta mission est de rédiger un résumé public d'épisode de campagne JDR à partir des informations fournies.\n\n"
        "Règles impératives :\n"
        "- Tu n'inventes aucun fait.\n"
        "- Tu n'ajoutes aucun personnage, lieu, objet ou événement absent des informations fournies.\n"
        "- Tu utilises uniquement le contexte transmis.\n"
        "- Si une information est absente, incertaine ou contradictoire, tu ne l'interprètes pas librement.\n"
        "- Tu rédiges en français.\n"
        "- Le style doit être narratif, fluide, clair et agréable à lire.\n"
        "- Le texte doit rester compréhensible pour les joueurs.\n"
        "- Tu ne mentionnes jamais les notes, logs, données, contexte, application, consignes ou modèle.\n"
        "- Tu ne produis ni titre, ni section, ni liste à puces.\n"
        "- Tu produis directement le résumé final.\n\n"
        "Objectif :\n"
        "- Un résumé public entre 250 et 500 mots.\n"
        "- Un texte continu en paragraphes.\n"
        "- Un ton d'aventure fantasy sobre et fidèle aux faits."
    )

    @staticmethod
    def generate_public_summary_for_episode(
        episode_id: int,
        triggered_by_user_id: int,
        send_email: bool = False,
        force_email: bool = False,
        force_regenerate: bool = False,
        allow_pending: bool = False,
        mark_pending: bool = True,
    ) -> dict[str, Any]:
        """Generer (ou reutiliser) un resume public pour un episode."""
        episode = Episode.query.get_or_404(episode_id)
        user = User.query.get_or_404(triggered_by_user_id)
        campaign = episode.story_arc.campaign

        EpisodeSummaryService._assert_can_manage_summary(user, campaign)

        source_payload = EpisodeSummaryService.build_public_source_payload(episode)
        source_hash = EpisodeSummaryService.compute_source_hash(source_payload)

        if episode.summary_status == 'pending' and not allow_pending:
            raise EpisodeSummaryAlreadyRunningError('Une generation est deja en cours pour cet episode.')

        if force_regenerate:
            episode.summary_source_hash = None

        if episode.summary_public and episode.summary_source_hash == source_hash and not force_regenerate:
            if episode.summary_status == 'pending':
                episode.summary_status = 'generated'
                episode.summary_generation_error = None
                db.session.commit()
            return {
                'summary': episode.summary_public,
                'skipped': True,
                'reason': 'unchanged_source',
                'source_hash': source_hash,
            }

        if mark_pending:
            episode.summary_status = 'pending'
            episode.summary_generation_error = None
            db.session.commit()

        try:
            user_prompt = EpisodeSummaryService.build_public_prompt_from_payload(source_payload)
            llm_output = OllamaService.generate_summary(
                system_prompt=EpisodeSummaryService.SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )
            summary_text = EpisodeSummaryService.normalize_summary_output(llm_output)

            if not summary_text:
                raise EpisodeSummaryGenerationError('Le resume genere est vide.')

            episode.summary_public = summary_text
            episode.summary_generated_at = datetime.utcnow()
            episode.summary_source_hash = source_hash
            episode.summary_status = 'generated'
            episode.summary_generation_error = None
            episode.summary_generated_by_user_id = user.id
            episode.summary_model_name = current_app.config.get('OLLAMA_MODEL', OllamaService.DEFAULT_MODEL)
            # Nouveau contenu: l'etat d'email repart a "not_sent" jusqu'au prochain envoi.
            episode.summary_email_status = 'not_sent'
            episode.summary_email_error = None
            db.session.commit()

        except Exception as exc:  # noqa: BLE001 - handling status transition and persistence
            episode.summary_status = 'failed'
            episode.summary_generation_error = str(exc)
            db.session.commit()
            if isinstance(exc, EpisodeSummaryError):
                raise
            raise EpisodeSummaryGenerationError(str(exc)) from exc

        result = {
            'summary': summary_text,
            'skipped': False,
            'source_hash': source_hash,
            'generated_at': episode.summary_generated_at,
            'model_name': episode.summary_model_name,
        }

        if send_email:
            try:
                email_result = EpisodeEmailService.send_episode_summary_email(
                    episode=episode,
                    source_hash=source_hash,
                    summary_text=summary_text,
                    force=force_email,
                )
                result['email'] = email_result
            except EpisodeEmailServiceError as exc:
                result['email'] = {'sent': False, 'error': str(exc)}
                result['email_error'] = str(exc)

        return result

    @staticmethod
    def enqueue_public_summary_generation(
        episode_id: int,
        triggered_by_user_id: int,
        send_email: bool = False,
        force_email: bool = False,
        force_regenerate: bool = False,
    ) -> None:
        """Lancer la generation de resume en arriere-plan puis retourner immediatement."""
        episode = Episode.query.get_or_404(episode_id)
        user = User.query.get_or_404(triggered_by_user_id)
        campaign = episode.story_arc.campaign
        EpisodeSummaryService._assert_can_manage_summary(user, campaign)

        if episode.summary_status == 'pending':
            raise EpisodeSummaryAlreadyRunningError('Une generation est deja en cours pour cet episode.')

        episode.summary_status = 'pending'
        episode.summary_generation_error = None
        db.session.commit()

        app = current_app._get_current_object()
        worker = threading.Thread(
            target=EpisodeSummaryService._run_public_summary_generation_job,
            kwargs={
                'app': app,
                'episode_id': episode_id,
                'triggered_by_user_id': triggered_by_user_id,
                'send_email': send_email,
                'force_email': force_email,
                'force_regenerate': force_regenerate,
            },
            daemon=True,
        )
        worker.start()

    @staticmethod
    def _run_public_summary_generation_job(
        app,
        episode_id: int,
        triggered_by_user_id: int,
        send_email: bool = False,
        force_email: bool = False,
        force_regenerate: bool = False,
    ) -> None:
        with app.app_context():
            try:
                result = EpisodeSummaryService.generate_public_summary_for_episode(
                    episode_id=episode_id,
                    triggered_by_user_id=triggered_by_user_id,
                    send_email=send_email,
                    force_email=force_email,
                    force_regenerate=force_regenerate,
                    allow_pending=True,
                    mark_pending=False,
                )
                episode = Episode.query.get(episode_id)
                if not episode:
                    return

                if result.get('email_error'):
                    NotificationService.create_notification(
                        triggered_by_user_id,
                        "Résumé d'épisode généré",
                        (
                            f'Le résumé de l\'épisode "{episode.title}" est disponible, '
                            f"mais l'envoi email a échoué : {result.get('email_error')}."
                        ),
                        kind='episode_summary',
                        campaign_id=episode.story_arc.campaign_id,
                    )
                else:
                    NotificationService.create_notification(
                        triggered_by_user_id,
                        "Résumé d'épisode généré",
                        f'Le résumé de l\'épisode "{episode.title}" est disponible.',
                        kind='episode_summary',
                        campaign_id=episode.story_arc.campaign_id,
                    )
            except Exception as exc:  # noqa: BLE001 - background job failure must always notify
                episode = Episode.query.get(episode_id)
                if episode:
                    episode.summary_status = 'failed'
                    episode.summary_generation_error = str(exc)
                    db.session.commit()
                    campaign_id = episode.story_arc.campaign_id
                    episode_title = episode.title
                else:
                    campaign_id = None
                    episode_title = str(episode_id)

                NotificationService.create_notification(
                    triggered_by_user_id,
                    "Échec de génération du résumé",
                    f'La génération du résumé de l\'épisode "{episode_title}" a échoué : {exc}',
                    kind='episode_summary',
                    campaign_id=campaign_id,
                )
            finally:
                db.session.remove()

    @staticmethod
    def build_public_source_payload(episode: Episode) -> dict[str, Any]:
        """Construire la charge source partageable (sans donnees privees)."""
        campaign = episode.story_arc.campaign
        player_notes = EpisodeSummaryService._collect_player_notes(episode.id)
        combats = EpisodeSummaryService._collect_combat_summaries(episode.id)

        return {
            'campaign': {
                'name': campaign.name,
            },
            'story_arc': {
                'name': episode.story_arc.name,
            },
            'episode': {
                'id': episode.id,
                'title': episode.title,
                'order_index': episode.order_index,
                'created_at': episode.created_at.isoformat() if episode.created_at else None,
            },
            'mj_notes': (episode.summary_shared or '').strip(),
            'player_notes': player_notes,
            'combats': combats,
        }

    @staticmethod
    def build_public_prompt_from_payload(source_payload: dict[str, Any]) -> str:
        """Transformer la charge source en prompt utilisateur structure."""
        return EpisodeSummaryService._render_source_payload_text(source_payload)

    @staticmethod
    def compute_source_hash(source_payload: dict[str, Any]) -> str:
        """Hasher les donnees sources pour detecter les changements."""
        normalized = json.dumps(source_payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    @staticmethod
    def normalize_summary_output(raw_text: str) -> str:
        """Nettoyer legerement la sortie LLM."""
        content = (raw_text or '').strip()
        if not content:
            return ''

        # Normaliser les espaces/lignes sans perdre la structure narrative.
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        normalized = '\n\n'.join(lines)

        # Garde-fou minimum pour eviter une reponse trop pauvre.
        if len(normalized) < 120:
            raise EpisodeSummaryGenerationError('Le resume genere est trop court pour etre exploitable.')

        return normalized

    @staticmethod
    def _assert_can_manage_summary(user: User, campaign) -> None:
        if user.role == 'Admin':
            return
        if not user.is_mj_of(campaign):
            raise EpisodeSummaryAccessError('Seul le MJ de la campagne peut generer le resume.')

    @staticmethod
    def _collect_player_notes(episode_id: int) -> list[dict[str, Any]]:
        notes = (
            EpisodeUserNote.query
            .join(User, User.id == EpisodeUserNote.user_id)
            .filter(
                EpisodeUserNote.episode_id == episode_id,
                EpisodeUserNote.notes.isnot(None),
                EpisodeUserNote.notes != '',
            )
            .order_by(EpisodeUserNote.updated_at.asc())
            .all()
        )

        return [
            {
                'username': note.user.username,
                'content': (note.notes or '').strip(),
                'updated_at': note.updated_at.isoformat() if note.updated_at else None,
            }
            for note in notes
            if (note.notes or '').strip()
        ]

    @staticmethod
    def _collect_combat_summaries(episode_id: int) -> list[dict[str, Any]]:
        combats = (
            Combat.query
            .filter_by(episode_id=episode_id)
            .order_by(Combat.created_at.asc(), Combat.id.asc())
            .all()
        )

        payload: list[dict[str, Any]] = []
        for idx, combat in enumerate(combats, start=1):
            participants_pj = [c.name for c in combat.combatants if (c.type or '').upper() == 'PJ']
            enemies = [c.name for c in combat.combatants if (c.type or '').upper() != 'PJ']

            notable_events = EpisodeSummaryService._extract_combat_notable_events(combat.id)
            issue = EpisodeSummaryService._infer_combat_issue(combat)

            payload.append({
                'order': idx,
                'name': combat.name or f'Combat {idx}',
                'participants_pj': participants_pj,
                'enemies': enemies,
                'notable_events': notable_events,
                'issue': issue,
            })

        return payload

    @staticmethod
    def _extract_combat_notable_events(combat_id: int, max_events: int = 6) -> list[str]:
        logs = (
            CombatLog.query
            .filter_by(combat_id=combat_id)
            .order_by(CombatLog.round_number.asc(), CombatLog.id.asc())
            .all()
        )

        notable: list[str] = []
        for log in logs:
            event = EpisodeSummaryService._format_notable_log(log)
            if event:
                notable.append(event)
            if len(notable) >= max_events:
                break

        return notable

    @staticmethod
    def _format_notable_log(log: CombatLog) -> str | None:
        action = (log.action_type or '').lower().strip()
        detail = (log.detail or '').strip()

        if action == 'damage' and log.value and log.value >= 10:
            return f'R{log.round_number}: degats importants ({log.value}).'

        if action == 'spell' and detail:
            return f'R{log.round_number}: sort marquant ({detail}).'

        if action in {'down', 'ko'}:
            return f'R{log.round_number}: un combattant tombe a 0 PV.'

        if action == 'death':
            return f'R{log.round_number}: un combattant est elimine.'

        if action == 'flee':
            return f'R{log.round_number}: un combattant prend la fuite.'

        if action == 'condition' and detail:
            return f'R{log.round_number}: condition notable ({detail}).'

        return None

    @staticmethod
    def _infer_combat_issue(combat: Combat) -> str:
        if not combat.combatants:
            return 'issue inconnue'

        enemies = [c for c in combat.combatants if (c.type or '').upper() != 'PJ']
        players = [c for c in combat.combatants if (c.type or '').upper() == 'PJ']

        enemy_alive = any(not c.is_dead and not c.has_fled for c in enemies)
        player_alive = any(not c.is_dead for c in players)

        if enemies and not enemy_alive and player_alive:
            return 'victoire des PJ'
        if players and not player_alive:
            return 'defaite des PJ'
        if any(c.has_fled for c in enemies):
            return 'ennemis en fuite'
        return 'issue incertaine'

    @staticmethod
    def _render_source_payload_text(source_payload: dict[str, Any]) -> str:
        campaign_name = source_payload.get('campaign', {}).get('name') or 'Campagne inconnue'
        arc_name = source_payload.get('story_arc', {}).get('name') or 'Arc non précisé'
        episode = source_payload.get('episode', {})
        episode_title = episode.get('title') or 'Épisode sans titre'
        episode_order = episode.get('order_index')
        episode_order_text = f' (ordre {episode_order})' if episode_order is not None else ''

        mj_notes = source_payload.get('mj_notes') or ''
        mj_notes_block = mj_notes.strip() if mj_notes.strip() else 'Aucune note MJ fournie.'

        player_notes = source_payload.get('player_notes') or []
        if player_notes:
            player_notes_lines = []
            for note in player_notes:
                username = note.get('username', 'Joueur')
                content = (note.get('content') or '').strip()
                if content:
                    player_notes_lines.append(f'- {username} : {content}')
            player_notes_block = '\n'.join(player_notes_lines) if player_notes_lines else 'Aucune note joueur disponible.'
        else:
            player_notes_block = 'Aucune note joueur disponible.'

        combats = source_payload.get('combats') or []
        if combats:
            combat_lines = []
            for combat in combats:
                order = combat.get('order')
                name = combat.get('name') or f'Combat {order}'
                pjs = ', '.join(combat.get('participants_pj') or []) or 'non renseignés'
                enemies = ', '.join(combat.get('enemies') or []) or 'non renseignés'
                issue = combat.get('issue') or 'issue inconnue'
                events = combat.get('notable_events') or []

                combat_lines.append(f'Combat {order} : {name}')
                combat_lines.append(f'- Participants PJ : {pjs}')
                combat_lines.append(f'- Ennemis : {enemies}')

                if events:
                    combat_lines.append('- Faits marquants :')
                    for event in events:
                        combat_lines.append(f'  - {event}')

                combat_lines.append(f'- Issue : {issue}')
                combat_lines.append('')
            combats_block = '\n'.join(combat_lines).strip()
        else:
            combats_block = 'Aucun combat rattaché à cet épisode.'

        return (
            'Tâche :\n'
            "Rédige un résumé narratif public de l'épisode ci-dessous.\n\n"
            'Priorité des informations :\n'
            '1. Notes du MJ\n'
            '2. Notes des joueurs\n'
            '3. Combats et faits marquants des combats\n\n'
            'Règles de traitement :\n'
            '- Utilise en priorité les faits présents dans les notes du MJ.\n'
            "- Complète avec les notes des joueurs uniquement lorsqu'elles apportent des éléments cohérents et utiles.\n"
            '- Utilise les combats pour intégrer les affrontements importants, leurs faits marquants et leur issue.\n'
            '- Respecte la chronologie générale suggérée par les informations fournies.\n'
            '- Si plusieurs sources expriment le même fait, ne le mentionne qu’une seule fois.\n'
            '- Si une information est ambiguë, isolée ou contradictoire, reformule-la avec prudence ou ignore-la.\n'
            '- Ne transforme jamais une hypothèse en certitude.\n'
            "- Conserve les noms propres exactement tels qu'ils apparaissent.\n"
            "- Mets l'accent sur les événements majeurs, les découvertes importantes, les tensions, les décisions et les combats significatifs.\n"
            "- N'ajoute aucun détail technique ou méta.\n\n"
            "Contexte de l'épisode :\n\n"
            '[IDENTITE]\n'
            f'Campagne : {campaign_name}\n'
            f'Arc : {arc_name}\n'
            f'Épisode : {episode_title}{episode_order_text}\n\n'
            '[NOTES_MJ]\n'
            f'{mj_notes_block}\n\n'
            '[NOTES_JOUEURS]\n'
            f'{player_notes_block}\n\n'
            '[COMBATS]\n'
            f'{combats_block}\n\n'
            'Résultat attendu :\n'
            "Rédige maintenant le résumé final de l'épisode, en français, sous forme de texte narratif continu, entre 250 et 500 mots."
        )
