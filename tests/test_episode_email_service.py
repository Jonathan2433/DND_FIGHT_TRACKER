from datetime import datetime
from types import SimpleNamespace

import pytest
from flask import Flask

from app.application.use_cases.episode_email_service import EpisodeEmailService, EpisodeEmailServiceError


@pytest.fixture
def app_context():
    app = Flask(__name__)
    app.config['BASE_URL'] = 'https://exalquest.app'
    app.config['MAIL_DEFAULT_SENDER'] = 'no-reply@exalquest.app'
    with app.app_context():
        yield app


def test_get_summary_recipients_includes_mj_and_unique_members(monkeypatch, app_context):
    campaign = SimpleNamespace(
        id=12,
        mj=SimpleNamespace(username='mj', email='mj@demo.test'),
    )

    memberships = [
        SimpleNamespace(user=SimpleNamespace(username='lyra', email='lyra@demo.test')),
        SimpleNamespace(user=SimpleNamespace(username='dorn', email='dorn@demo.test')),
        SimpleNamespace(user=SimpleNamespace(username='dupe', email='LYRA@demo.test')),
    ]

    monkeypatch.setattr(
        'app.application.use_cases.episode_email_service.CampaignMember.query',
        SimpleNamespace(filter_by=lambda **_kwargs: SimpleNamespace(all=lambda: memberships)),
    )

    recipients = EpisodeEmailService.get_summary_recipients(campaign)

    assert [entry['email'] for entry in recipients] == [
        'mj@demo.test',
        'lyra@demo.test',
        'dorn@demo.test',
    ]


def test_send_episode_summary_email_skips_if_hash_already_emailed(app_context):
    episode = SimpleNamespace(
        id=3,
        title='Le sceau brise',
        order_index=7,
        summary_public='Resume deja envoye',
        summary_email_status='not_sent',
        summary_last_emailed_hash='abc',
    )

    result = EpisodeEmailService.send_episode_summary_email(episode=episode, source_hash='abc')

    assert result['sent'] is False
    assert result['skipped'] is True
    assert result['reason'] == 'unchanged_summary_already_emailed'


def test_send_episode_summary_email_updates_episode_on_success(monkeypatch, app_context):
    campaign = SimpleNamespace(
        id=99,
        name='Les Ombres de Valdorne',
        mj=SimpleNamespace(username='MJ', email='mj@demo.test'),
    )
    episode = SimpleNamespace(
        id=77,
        title='Episode 7 - Le sceau brise',
        order_index=7,
        summary_public='Un long resume ' * 20,
        summary_email_status='not_sent',
        summary_email_error=None,
        summary_last_emailed_at=None,
        summary_last_emailed_hash=None,
        story_arc=SimpleNamespace(campaign=campaign),
    )

    commits = {'count': 0}
    monkeypatch.setattr(
        'app.application.use_cases.episode_email_service.db.session',
        SimpleNamespace(commit=lambda: commits.__setitem__('count', commits['count'] + 1)),
    )
    monkeypatch.setattr(
        EpisodeEmailService,
        'get_summary_recipients',
        staticmethod(lambda _campaign: [
            {'email': 'mj@demo.test', 'username': 'MJ'},
            {'email': 'lyra@demo.test', 'username': 'Lyra'},
        ]),
    )
    monkeypatch.setattr(
        'app.application.use_cases.episode_email_service.EmailService._send_message',
        staticmethod(lambda msg, _ctx: {'success': True, 'recipients': msg.recipients}),
    )

    result = EpisodeEmailService.send_episode_summary_email(episode=episode, source_hash='hash-1')

    assert result['sent'] is True
    assert result['recipient_count'] == 2
    assert episode.summary_email_status == 'sent'
    assert episode.summary_last_emailed_hash == 'hash-1'
    assert isinstance(episode.summary_last_emailed_at, datetime)
    assert commits['count'] == 2


def test_send_episode_summary_email_fails_with_empty_summary(monkeypatch, app_context):
    campaign = SimpleNamespace(id=1, name='Campagne test', mj=SimpleNamespace(username='MJ', email='mj@demo.test'))
    episode = SimpleNamespace(
        id=5,
        title='Episode vide',
        summary_public=' ',
        summary_email_status='not_sent',
        summary_email_error=None,
        summary_last_emailed_hash=None,
        story_arc=SimpleNamespace(campaign=campaign),
    )

    commits = {'count': 0}
    monkeypatch.setattr(
        'app.application.use_cases.episode_email_service.db.session',
        SimpleNamespace(commit=lambda: commits.__setitem__('count', commits['count'] + 1)),
    )

    with pytest.raises(EpisodeEmailServiceError, match='Resume vide'):
        EpisodeEmailService.send_episode_summary_email(episode=episode, source_hash='hash')

    assert episode.summary_email_status == 'failed'
    assert commits['count'] == 1


def test_send_episode_summary_email_refuses_when_pending(app_context):
    episode = SimpleNamespace(
        id=9,
        title='Episode verrouille',
        summary_public='Un resume deja pret.',
        summary_email_status='pending',
        summary_last_emailed_hash=None,
    )

    with pytest.raises(EpisodeEmailServiceError, match='deja en cours'):
        EpisodeEmailService.send_episode_summary_email(episode=episode, source_hash='hash-pending')
