import time

import redis
from fastapi import HTTPException, Request, status

from app.core.config import settings

redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


def enforce_ai_rate_limit(request: Request) -> None:
    client_host = request.client.host if request.client else "unknown"

    window_seconds = settings.ai_rate_limit_window_seconds
    current_time = int(time.time())
    current_window = current_time // window_seconds

    key = f"rate-limit:ai:{client_host}:{current_window}"

    try:
        with redis_client.pipeline(transaction=True) as pipeline:
            pipeline.incr(key)
            pipeline.expire(key, window_seconds)

            request_count, _ = pipeline.execute()

    except redis.RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting service is unavailable.",
        ) from exc

    if request_count > settings.ai_rate_limit_requests:
        retry_after = window_seconds - (current_time % window_seconds)

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI request rate limit exceeded.",
            headers={"Retry-After": str(retry_after)},
        )