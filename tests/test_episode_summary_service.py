from datetime import datetime
from types import SimpleNamespace

import pytest
from flask import Flask

from app.application.use_cases.episode_summary_service import (
    EpisodeSummaryAlreadyRunningError,
    EpisodeSummaryGenerationError,
    EpisodeSummaryService,
)


def test_compute_source_hash_is_stable_for_same_payload_content():
    payload_a = {'b': 2, 'a': {'x': 1, 'y': [3, 4]}}
    payload_b = {'a': {'y': [3, 4], 'x': 1}, 'b': 2}

    assert EpisodeSummaryService.compute_source_hash(payload_a) == EpisodeSummaryService.compute_source_hash(payload_b)


def test_build_public_prompt_contains_key_sections():
    payload = {
        'campaign': {'name': 'Les Ombres de Valdorne'},
        'story_arc': {'name': 'La crypte oubliee'},
        'episode': {'title': 'Episode 7 - Le sceau brise', 'order_index': 7},
        'mj_notes': 'Le sceau demoniaque cede.',
        'player_notes': [{'username': 'Lyra', 'content': 'J\'ai inspecte l\'autel.'}],
        'combats': [{
            'order': 1,
            'name': 'Gardien spectral',
            'participants_pj': ['Arthas', 'Lyra'],
            'enemies': ['Gardien spectral'],
            'notable_events': ['R2: un combattant tombe a 0 PV.'],
            'issue': 'victoire des PJ',
        }],
    }

    prompt = EpisodeSummaryService.build_public_prompt_from_payload(payload)

    assert 'Campagne : Les Ombres de Valdorne' in prompt
    assert 'Notes du MJ :' in prompt
    assert 'Lyra' in prompt
    assert 'Combat 1 : Gardien spectral' in prompt
    assert 'Consignes :' in prompt


def test_normalize_summary_output_rejects_too_short_content():
    with pytest.raises(EpisodeSummaryGenerationError, match='trop court'):
        EpisodeSummaryService.normalize_summary_output('Trop court.')


def test_generate_public_summary_skips_when_source_unchanged(monkeypatch):
    app = Flask(__name__)
    with app.app_context():
        episode = SimpleNamespace(
            id=1,
            summary_public='Resume deja present',
            summary_source_hash='abc',
            summary_status='generated',
            story_arc=SimpleNamespace(campaign=SimpleNamespace(mj_id=42)),
        )
        user = SimpleNamespace(id=42, role='MJ', is_mj_of=lambda campaign: True)

        monkeypatch.setattr('app.application.use_cases.episode_summary_service.Episode.query', SimpleNamespace(get_or_404=lambda _id: episode))
        monkeypatch.setattr('app.application.use_cases.episode_summary_service.User.query', SimpleNamespace(get_or_404=lambda _id: user))
        monkeypatch.setattr(EpisodeSummaryService, 'build_public_source_payload', staticmethod(lambda _episode: {'k': 'v'}))
        monkeypatch.setattr(EpisodeSummaryService, 'compute_source_hash', staticmethod(lambda _payload: 'abc'))

        result = EpisodeSummaryService.generate_public_summary_for_episode(1, 42)

        assert result['skipped'] is True
        assert result['reason'] == 'unchanged_source'


def test_generate_public_summary_refuses_when_pending(monkeypatch):
    app = Flask(__name__)
    with app.app_context():
        episode = SimpleNamespace(
            id=1,
            summary_public=None,
            summary_source_hash=None,
            summary_status='pending',
            story_arc=SimpleNamespace(campaign=SimpleNamespace(mj_id=42)),
        )
        user = SimpleNamespace(id=42, role='MJ', is_mj_of=lambda campaign: True)

        monkeypatch.setattr('app.application.use_cases.episode_summary_service.Episode.query', SimpleNamespace(get_or_404=lambda _id: episode))
        monkeypatch.setattr('app.application.use_cases.episode_summary_service.User.query', SimpleNamespace(get_or_404=lambda _id: user))
        monkeypatch.setattr(EpisodeSummaryService, 'build_public_source_payload', staticmethod(lambda _episode: {'k': 'v'}))
        monkeypatch.setattr(EpisodeSummaryService, 'compute_source_hash', staticmethod(lambda _payload: 'new'))

        with pytest.raises(EpisodeSummaryAlreadyRunningError):
            EpisodeSummaryService.generate_public_summary_for_episode(1, 42)


def test_generate_public_summary_success_updates_episode(monkeypatch):
    app = Flask(__name__)
    app.config['OLLAMA_MODEL'] = 'llama3.2:1b'

    with app.app_context():
        campaign = SimpleNamespace(mj_id=42)
        episode = SimpleNamespace(
            id=1,
            summary_public=None,
            summary_source_hash=None,
            summary_status='not_generated',
            summary_generation_error=None,
            summary_generated_at=None,
            summary_generated_by_user_id=None,
            summary_model_name=None,
            story_arc=SimpleNamespace(campaign=campaign),
        )
        user = SimpleNamespace(id=42, role='MJ', is_mj_of=lambda _campaign: True)

        commits = {'count': 0}

        monkeypatch.setattr('app.application.use_cases.episode_summary_service.Episode.query', SimpleNamespace(get_or_404=lambda _id: episode))
        monkeypatch.setattr('app.application.use_cases.episode_summary_service.User.query', SimpleNamespace(get_or_404=lambda _id: user))
        monkeypatch.setattr(
            'app.application.use_cases.episode_summary_service.db.session',
            SimpleNamespace(commit=lambda: commits.__setitem__('count', commits['count'] + 1)),
        )
        monkeypatch.setattr(EpisodeSummaryService, 'build_public_source_payload', staticmethod(lambda _episode: {'k': 'v'}))
        monkeypatch.setattr(EpisodeSummaryService, 'compute_source_hash', staticmethod(lambda _payload: 'hash-1'))
        monkeypatch.setattr(EpisodeSummaryService, 'build_public_prompt_from_payload', staticmethod(lambda _payload: 'PROMPT'))
        monkeypatch.setattr(
            'app.application.use_cases.episode_summary_service.OllamaService.generate_summary',
            staticmethod(lambda **kwargs: ' '.join(['resume'] * 40)),
        )

        result = EpisodeSummaryService.generate_public_summary_for_episode(1, 42)

        assert result['skipped'] is False
        assert episode.summary_status == 'generated'
        assert episode.summary_source_hash == 'hash-1'
        assert episode.summary_generated_by_user_id == 42
        assert episode.summary_model_name == 'llama3.2:1b'
        assert isinstance(episode.summary_generated_at, datetime)
        assert commits['count'] == 2
