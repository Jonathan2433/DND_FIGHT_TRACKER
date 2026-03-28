"""Service d'acces a l'API Ollama."""
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from flask import current_app


class OllamaServiceError(RuntimeError):
    """Erreur de base du service Ollama."""


class OllamaConfigurationError(OllamaServiceError):
    """Configuration Ollama invalide."""


class OllamaRequestError(OllamaServiceError):
    """Erreur d'appel a Ollama."""


class OllamaService:
    """Client applicatif pour les generations via Ollama."""

    DEFAULT_BASE_URL = "http://127.0.0.1:11434"
    DEFAULT_MODEL = "llama3.2:1b"
    DEFAULT_TIMEOUT_SECONDS = 120
    DEFAULT_TEMPERATURE = 0.4

    @staticmethod
    def generate_summary(system_prompt, user_prompt, model=None, temperature=None, keep_alive="10m"):
        """Generer un resume a partir d'un prompt systeme et utilisateur."""
        messages = [
            {"role": "system", "content": system_prompt or ""},
            {"role": "user", "content": user_prompt or ""},
        ]
        return OllamaService.generate_chat(
            messages=messages,
            model=model,
            temperature=temperature,
            keep_alive=keep_alive,
        )

    @staticmethod
    def generate_chat(messages, model=None, temperature=None, keep_alive="10m", timeout_seconds=None):
        """Generer une reponse de chat Ollama et retourner uniquement le texte."""
        if not isinstance(messages, list) or not messages:
            raise OllamaConfigurationError("Le payload Ollama requiert une liste 'messages' non vide.")

        selected_model = model or OllamaService._get_config("OLLAMA_MODEL", OllamaService.DEFAULT_MODEL)
        if not selected_model:
            raise OllamaConfigurationError("OLLAMA_MODEL est requis pour appeler Ollama.")

        endpoint = OllamaService._build_chat_endpoint()
        payload = {
            "model": selected_model,
            "messages": messages,
            "stream": False,
            "keep_alive": keep_alive,
            "options": {
                "temperature": (
                    OllamaService.DEFAULT_TEMPERATURE
                    if temperature is None
                    else temperature
                )
            },
        }

        body = json.dumps(payload).encode("utf-8")
        request = Request(
            endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        timeout = timeout_seconds
        if timeout is None:
            timeout = int(
                OllamaService._get_config(
                    "OLLAMA_TIMEOUT_SECONDS",
                    OllamaService.DEFAULT_TIMEOUT_SECONDS,
                )
            )

        try:
            with urlopen(request, timeout=timeout) as response:
                response_body = response.read().decode("utf-8")
        except HTTPError as exc:
            error_body = ""
            try:
                error_body = exc.read().decode("utf-8")
            except Exception:
                error_body = ""
            raise OllamaRequestError(
                f"Erreur HTTP Ollama ({exc.code}): {error_body or exc.reason}"
            ) from exc
        except URLError as exc:
            raise OllamaRequestError(f"Ollama indisponible: {exc.reason}") from exc
        except TimeoutError as exc:
            raise OllamaRequestError("Timeout lors de l'appel Ollama.") from exc

        try:
            parsed = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise OllamaRequestError("Reponse Ollama invalide (JSON illisible).") from exc

        content = ((parsed.get("message") or {}).get("content") or "").strip()
        if not content:
            raise OllamaRequestError("Ollama a retourne une reponse vide.")

        return content

    @staticmethod
    def _build_chat_endpoint():
        base_url = OllamaService._get_config("OLLAMA_BASE_URL", OllamaService.DEFAULT_BASE_URL)
        if not base_url:
            raise OllamaConfigurationError("OLLAMA_BASE_URL est requis.")
        normalized = base_url if str(base_url).endswith("/") else f"{base_url}/"
        return urljoin(normalized, "api/chat")

    @staticmethod
    def _get_config(key, default=None):
        return current_app.config.get(key, default)
