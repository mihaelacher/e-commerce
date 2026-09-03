from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, Request
from redis.exceptions import RedisError

from app.core import rate_limit


@pytest.mark.anyio
async def test_ai_rate_limit_rejects_requests_over_limit(monkeypatch):
    current_time = 120.0

    class FakePipeline:
        def __init__(self):
            self.request_count = 0
            self.incr = AsyncMock(side_effect=self._incr)
            self.expire = AsyncMock()
            self.execute = AsyncMock(side_effect=self._execute)

        async def _incr(self, key):
            self.request_count += 1

        async def _execute(self):
            return self.request_count, True

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

    class FakeRedis:
        def __init__(self):
            self.pipeline_instance = FakePipeline()

        def pipeline(self, transaction=True):
            return self.pipeline_instance

    redis = FakeRedis()
    monkeypatch.setattr(rate_limit.time, "time", lambda: current_time)
    monkeypatch.setattr(rate_limit.settings, "ai_rate_limit_requests", 1)
    monkeypatch.setattr(rate_limit.settings, "ai_rate_limit_window_seconds", 60)

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/ai/chat",
            "headers": [],
            "client": ("127.0.0.1", 12345),
        }
    )

    await rate_limit.enforce_ai_rate_limit(request, redis)

    with pytest.raises(HTTPException) as error:
        await rate_limit.enforce_ai_rate_limit(request, redis)

    assert error.value.status_code == 429
    assert error.value.headers["Retry-After"] == "60"


class FakePipeline:
    def __init__(self, request_count: int):
        self.request_count = request_count
        self.incr = AsyncMock()
        self.expire = AsyncMock()
        self.execute = AsyncMock(return_value=(request_count, True))

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None


class FakeRedis:
    def __init__(self, pipeline: FakePipeline):
        self.pipeline_instance = pipeline

    def pipeline(self, transaction=True):
        assert transaction is True
        return self.pipeline_instance


def make_request(host: str = "127.0.0.1") -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/ai/chat",
            "headers": [],
            "client": (host, 12345),
        }
    )


@pytest.mark.anyio
async def test_ai_rate_limit_allows_request(monkeypatch):
    pipeline = FakePipeline(request_count=1)
    redis = FakeRedis(pipeline)
    monkeypatch.setattr(rate_limit.settings, "ai_rate_limit_requests", 2)

    await rate_limit.enforce_ai_rate_limit(make_request(), redis)

    pipeline.incr.assert_awaited_once()
    pipeline.expire.assert_awaited_once()
    pipeline.execute.assert_awaited_once()


@pytest.mark.anyio
async def test_ai_rate_limit_rejects_excess_requests(monkeypatch):
    pipeline = FakePipeline(request_count=3)
    redis = FakeRedis(pipeline)
    monkeypatch.setattr(rate_limit.settings, "ai_rate_limit_requests", 2)

    with pytest.raises(HTTPException) as exc_info:
        await rate_limit.enforce_ai_rate_limit(make_request(), redis)

    assert exc_info.value.status_code == 429
    assert exc_info.value.headers["Retry-After"]


@pytest.mark.anyio
async def test_ai_rate_limit_returns_service_unavailable_on_redis_error():
    pipeline = FakePipeline(request_count=1)
    pipeline.execute.side_effect = RedisError("Redis unavailable")
    redis = FakeRedis(pipeline)

    with pytest.raises(HTTPException) as exc_info:
        await rate_limit.enforce_ai_rate_limit(make_request(), redis)

    assert exc_info.value.status_code == 503
