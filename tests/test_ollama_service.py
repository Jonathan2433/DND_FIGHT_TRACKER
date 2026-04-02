import json

import pytest
from flask import Flask

from app.application.use_cases import ollama_service as ollama_module
from app.application.use_cases.ollama_service import OllamaRequestError, OllamaService


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.fixture
def app_context():
    app = Flask(__name__)
    app.config.update(
        OLLAMA_BASE_URL='http://localhost:11434',
        OLLAMA_MODEL='llama3.2:1b',
        OLLAMA_TIMEOUT_SECONDS=42,
    )
    with app.app_context():
        yield app


def test_generate_chat_builds_expected_payload(monkeypatch, app_context):
    captured = {}

    def fake_urlopen(request, timeout):
        captured['url'] = request.full_url
        captured['timeout'] = timeout
        captured['payload'] = json.loads(request.data.decode('utf-8'))
        return _FakeResponse(json.dumps({'message': {'content': 'Résumé ok'}}).encode('utf-8'))

    monkeypatch.setattr(ollama_module, 'urlopen', fake_urlopen)

    content = OllamaService.generate_chat(
        messages=[{'role': 'user', 'content': 'Bonjour'}],
        keep_alive='10m',
    )

    assert content == 'Résumé ok'
    assert captured['url'] == 'http://localhost:11434/api/chat'
    assert captured['timeout'] == 42
    assert captured['payload']['model'] == 'llama3.2:1b'
    assert captured['payload']['stream'] is False
    assert captured['payload']['keep_alive'] == '10m'
    assert captured['payload']['options']['temperature'] == 0.4


def test_generate_summary_creates_system_and_user_messages(monkeypatch, app_context):
    captured = {}

    def fake_generate_chat(messages, model=None, temperature=None, keep_alive='10m', timeout_seconds=None):
        captured['messages'] = messages
        captured['model'] = model
        captured['temperature'] = temperature
        captured['keep_alive'] = keep_alive
        captured['timeout_seconds'] = timeout_seconds
        return 'Texte final'

    monkeypatch.setattr(OllamaService, 'generate_chat', staticmethod(fake_generate_chat))

    output = OllamaService.generate_summary('SYS', 'USR', model='mistral', temperature=0.2)

    assert output == 'Texte final'
    assert captured['messages'] == [
        {'role': 'system', 'content': 'SYS'},
        {'role': 'user', 'content': 'USR'},
    ]
    assert captured['model'] == 'mistral'
    assert captured['temperature'] == 0.2


def test_generate_chat_raises_on_empty_content(monkeypatch, app_context):
    def fake_urlopen(_request, timeout):
        return _FakeResponse(json.dumps({'message': {'content': '   '}}).encode('utf-8'))

    monkeypatch.setattr(ollama_module, 'urlopen', fake_urlopen)

    with pytest.raises(OllamaRequestError, match='reponse vide'):
        OllamaService.generate_chat(messages=[{'role': 'user', 'content': 'Bonjour'}])


def test_generate_chat_retries_localhost_and_127(monkeypatch, app_context):
    called_urls = []

    def fake_urlopen(request, timeout):
        called_urls.append(request.full_url)
        if request.full_url.startswith('http://localhost:11434'):
            raise ollama_module.URLError(ConnectionRefusedError(111, 'Connection refused'))
        return _FakeResponse(json.dumps({'message': {'content': 'OK fallback'}}).encode('utf-8'))

    monkeypatch.setattr(ollama_module, 'urlopen', fake_urlopen)

    content = OllamaService.generate_chat(messages=[{'role': 'user', 'content': 'Bonjour'}])

    assert content == 'OK fallback'
    assert called_urls == [
        'http://localhost:11434/api/chat',
        'http://127.0.0.1:11434/api/chat',
    ]


def test_generate_chat_unavailable_lists_tested_endpoints(monkeypatch, app_context):
    app_context.config['OLLAMA_FALLBACK_BASE_URLS'] = 'http://ollama:11434'

    def fake_urlopen(_request, timeout):
        raise ollama_module.URLError(ConnectionRefusedError(111, 'Connection refused'))

    monkeypatch.setattr(ollama_module, 'urlopen', fake_urlopen)

    with pytest.raises(OllamaRequestError, match='Endpoints testes'):
        OllamaService.generate_chat(messages=[{'role': 'user', 'content': 'Bonjour'}])
