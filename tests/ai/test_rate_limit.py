from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core import rate_limit


def test_ai_rate_limit_rejects_requests_over_limit(monkeypatch):
    calls = {}
    current_time = 120.0

    class FakePipeline:
        def incr(self, key):
            calls[key] = calls.get(key, 0) + 1
            return self

        def expire(self, key, seconds):
            return self

        def execute(self):
            return calls[next(iter(calls))], True

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    class FakeRedis:
        def pipeline(self, transaction=True):
            return FakePipeline()

    monkeypatch.setattr(rate_limit, "redis_client", FakeRedis())
    monkeypatch.setattr(rate_limit.time, "time", lambda: current_time)
    monkeypatch.setattr(rate_limit.settings, "ai_rate_limit_requests", 1)
    monkeypatch.setattr(rate_limit.settings, "ai_rate_limit_window_seconds", 60)

    request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))

    rate_limit.enforce_ai_rate_limit(request)

    with pytest.raises(HTTPException) as error:
        rate_limit.enforce_ai_rate_limit(request)

    assert error.value.status_code == 429
    assert error.value.headers["Retry-After"] == "60"
