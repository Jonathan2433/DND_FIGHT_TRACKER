from datetime import datetime
from types import SimpleNamespace

import pytest
from flask import Flask

from app.application.use_cases.auth_service import AuthService


@pytest.fixture
def app_context():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'
    with app.app_context():
        yield app


def test_request_password_reset_returns_generic_when_user_not_found(monkeypatch, app_context):
    fake_user_model = SimpleNamespace(
        username='username',
        email='email',
        query=SimpleNamespace(filter=lambda *_args, **_kwargs: SimpleNamespace(first=lambda: None)),
    )
    monkeypatch.setattr('app.application.use_cases.auth_service.User', fake_user_model)

    result = AuthService.request_password_reset('unknown@example.com', request_ip='127.0.0.1')

    assert result['success'] is True
    assert 'Si un compte existe' in result['message']


def test_validate_password_reset_token_rejects_used_or_expired(monkeypatch, app_context):
    used_token = SimpleNamespace(
        is_used=True,
        is_expired=False,
        user=SimpleNamespace(is_active=True),
    )
    monkeypatch.setattr(
        'app.application.use_cases.auth_service.PasswordResetToken.find_by_raw_token',
        staticmethod(lambda _token: used_token),
    )
    used_result = AuthService.validate_password_reset_token('abc')
    assert 'error' in used_result

    expired_token = SimpleNamespace(
        is_used=False,
        is_expired=True,
        user=SimpleNamespace(is_active=True),
    )
    monkeypatch.setattr(
        'app.application.use_cases.auth_service.PasswordResetToken.find_by_raw_token',
        staticmethod(lambda _token: expired_token),
    )
    expired_result = AuthService.validate_password_reset_token('abc')
    assert 'expire' in expired_result['error']


def test_password_reset_rate_limited(monkeypatch, app_context):
    query = SimpleNamespace(filter=lambda *args, **kwargs: SimpleNamespace(scalar=lambda: 3))
    monkeypatch.setattr('app.application.use_cases.auth_service.db.session.query', lambda *_args, **_kwargs: query)

    assert AuthService._password_reset_rate_limited(user_id=1) is True
