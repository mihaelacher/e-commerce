import httpx
import pytest

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