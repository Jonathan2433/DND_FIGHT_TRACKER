from types import SimpleNamespace

from flask import Flask

from app.web.routes.notification import _notification_target


def _build_app():
    app = Flask(__name__)
    app.add_url_rule('/episode/<int:episode_id>', endpoint='episode.view_episode', view_func=lambda episode_id: str(episode_id))
    app.add_url_rule('/campaign/<int:campaign_id>', endpoint='campaign.view_campaign', view_func=lambda campaign_id: str(campaign_id))
    app.add_url_rule('/campaign/<int:campaign_id>/review', endpoint='campaign.review_invitation', view_func=lambda campaign_id: str(campaign_id))
    app.add_url_rule('/', endpoint='main.index', view_func=lambda: 'index')
    app.add_url_rule('/templates', endpoint='template.manage_templates', view_func=lambda: 'templates')
    app.add_url_rule('/combat/player/<int:combat_id>', endpoint='combat.view_combat_player', view_func=lambda combat_id: str(combat_id))
    app.add_url_rule('/combat/<int:combat_id>/summary', endpoint='summary.combat_summary', view_func=lambda combat_id: str(combat_id))
    return app


def test_notification_target_redirects_episode_summary_to_episode_page():
    app = _build_app()

    with app.test_request_context():
        notification = SimpleNamespace(kind='episode_summary:42', campaign_id=3)

        target = _notification_target(user_id=1, notification=notification)

        assert target == '/episode/42'


def test_notification_target_keeps_campaign_fallback_for_legacy_episode_summary_kind():
    app = _build_app()

    with app.test_request_context():
        notification = SimpleNamespace(kind='episode_summary', campaign_id=7)

        target = _notification_target(user_id=1, notification=notification)

        assert target == '/'
