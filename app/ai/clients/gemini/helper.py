import time

import httpx
from google.genai import errors

from app.exceptions.ai import AIProviderUnavailableError

RETRYABLE_EXCEPTIONS = (
    httpx.RemoteProtocolError,
    httpx.TimeoutException,
    httpx.ConnectError,
    errors.ServerError,
)


def with_retry(func):
    max_attempts = 4

    for attempt in range(max_attempts):
        try:
            return func()

        except RETRYABLE_EXCEPTIONS as exc:
            if attempt == max_attempts - 1:
                raise AIProviderUnavailableError(
                    "AI provider is temporarily unavailable."
                ) from exc

            time.sleep(2 ** attempt)