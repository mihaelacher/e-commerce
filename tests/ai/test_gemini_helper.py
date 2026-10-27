import httpx
import pytest

from app.ai.clients.gemini.client import GeminiClient
from app.ai.clients.gemini.embedding import GeminiEmbeddingClient
from app.ai.clients.gemini.helper import with_retry
from app.exceptions.ai import AIProviderUnavailableError


def test_with_retry_retries_transient_provider_errors(monkeypatch):
    attempts = 0
    sleep_delays = []

    def request():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise httpx.ConnectError("provider unavailable")
        return "success"

    monkeypatch.setattr("app.ai.clients.gemini.helper.time.sleep", sleep_delays.append)

    assert with_retry(request) == "success"
    assert attempts == 3
    assert sleep_delays == [1, 2]


def test_with_retry_raises_application_error_after_exhaustion(monkeypatch):
    monkeypatch.setattr("app.ai.clients.gemini.helper.time.sleep", lambda _: None)

    def request():
        raise httpx.ConnectError("provider unavailable")

    with pytest.raises(AIProviderUnavailableError):
        with_retry(request)


@pytest.mark.parametrize(
    "client_class",
    [GeminiClient, GeminiEmbeddingClient],
)
def test_gemini_clients_require_provider_key(monkeypatch, client_class):
    monkeypatch.setattr("app.core.config.settings.gemini_api_key", None)

    with pytest.raises(AIProviderUnavailableError, match="GEMINI_API_KEY"):
        client_class()
