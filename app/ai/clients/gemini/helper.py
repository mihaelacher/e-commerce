import asyncio
import time

import httpx
from google.genai import errors

from app.core.config import settings
from app.core.logging import get_logger
from app.exceptions.ai import AIProviderUnavailableError

logger = get_logger(__name__)

RETRYABLE_EXCEPTIONS = (
    httpx.RemoteProtocolError,
    httpx.TimeoutException,
    httpx.ConnectError,
    errors.ServerError,
)


def with_retry(func):
    max_attempts = settings.ai_provider_max_attempts

    for attempt in range(max_attempts):
        try:
            return func()

        except errors.ClientError as exc:
            if exc.code == 429:
                logger.warning(
                    "ai_retry_rate_limited",
                    extra={
                        "attempt": attempt + 1,
                        "max_attempts": max_attempts,
                    },
                )

                raise AIProviderUnavailableError(
                    "AI provider quota has been exceeded."
                ) from exc

            logger.exception(
                "ai_retry_client_error",
                extra={
                    "attempt": attempt + 1,
                    "max_attempts": max_attempts,
                },
            )
            raise

        except RETRYABLE_EXCEPTIONS as exc:
            if attempt == max_attempts - 1:
                logger.exception(
                    "ai_retry_exhausted",
                    extra={
                        "attempt": attempt + 1,
                        "max_attempts": max_attempts,
                    },
                )

                raise AIProviderUnavailableError(
                    "AI provider is temporarily unavailable."
                ) from exc

            delay_seconds = 2**attempt

            logger.warning(
                "ai_retrying_after_transient_error",
                extra={
                    "attempt": attempt + 1,
                    "max_attempts": max_attempts,
                    "delay_seconds": delay_seconds,
                    "exception_type": type(exc).__name__,
                },
            )

            time.sleep(delay_seconds)


async def with_retry_async(func):
    max_attempts = settings.ai_provider_max_attempts

    for attempt in range(max_attempts):
        try:
            return await func()

        except errors.ClientError as exc:
            if exc.code == 429:
                logger.warning(
                    "ai_retry_rate_limited",
                    extra={
                        "attempt": attempt + 1,
                        "max_attempts": max_attempts,
                    },
                )

                raise AIProviderUnavailableError(
                    "AI provider quota has been exceeded."
                ) from exc

            logger.exception(
                "ai_retry_client_error",
                extra={
                    "attempt": attempt + 1,
                    "max_attempts": max_attempts,
                },
            )
            raise

        except RETRYABLE_EXCEPTIONS as exc:
            if attempt == max_attempts - 1:
                logger.exception(
                    "ai_retry_exhausted",
                    extra={
                        "attempt": attempt + 1,
                        "max_attempts": max_attempts,
                    },
                )

                raise AIProviderUnavailableError(
                    "AI provider is temporarily unavailable."
                ) from exc

            delay_seconds = 2**attempt

            logger.warning(
                "ai_retrying_after_transient_error",
                extra={
                    "attempt": attempt + 1,
                    "max_attempts": max_attempts,
                    "delay_seconds": delay_seconds,
                    "exception_type": type(exc).__name__,
                },
            )

            await asyncio.sleep(delay_seconds)
