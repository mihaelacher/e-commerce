import time
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.dependencies.core import get_redis


async def enforce_ai_rate_limit(
    request: Request,
    redis: Annotated[Redis, Depends(get_redis)],
) -> None:
    client_host = request.client.host if request.client else "unknown"

    window_seconds = settings.ai_rate_limit_window_seconds
    current_time = int(time.time())
    current_window = current_time // window_seconds

    key = f"rate-limit:ai:{client_host}:{current_window}"

    try:
        async with redis.pipeline(transaction=True) as pipeline:
            await pipeline.incr(key)
            await pipeline.expire(key, window_seconds)

            request_count, _ = await pipeline.execute()

    except RedisError as exc:
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
