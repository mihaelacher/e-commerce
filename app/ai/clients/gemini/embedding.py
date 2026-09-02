import time

from google import genai
from google.genai import types

from app.ai.clients.embedding_base import EmbeddingClient
from app.ai.clients.gemini.helper import with_retry, with_retry_async
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiEmbeddingClient(EmbeddingClient):
    def __init__(self) -> None:
        self.model = "gemini-embedding-2"
        self.client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(
                timeout=settings.ai_client_timeout_ms,
            ),
        )

    def embed(self, text: str) -> list[float]:
        start_time = time.perf_counter()

        def request():
            response = self.client.models.embed_content(
                model=self.model,
                contents=text,
                config=types.EmbedContentConfig(
                    output_dimensionality=768,
                ),
            )

            embedding = response.embeddings[0].values

            logger.info(
                "embedding_completed",
                extra={
                    "provider": "gemini",
                    "model": self.model,
                    "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
                },
            )

            return embedding

        try:
            return with_retry(request)
        except Exception:
            logger.exception(
                "embedding_failed",
                extra={
                    "provider": "gemini",
                    "model": self.model,
                    "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
                },
            )
            raise


    async def embed_async(
        self,
        text: str,
    ) -> list[float]:
        start_time = time.perf_counter()

        async def request():
            response = await self.client.aio.models.embed_content(
                model=self.model,
                contents=text,
                config=types.EmbedContentConfig(
                    output_dimensionality=768,
                ),
            )

            embedding = response.embeddings[0].values

            logger.info(
                "embedding_completed",
                extra={
                    "provider": "gemini",
                    "model": self.model,
                    "duration_ms": round(
                        (time.perf_counter() - start_time) * 1000,
                        2,
                    ),
                },
            )

            return embedding

        try:
            return await with_retry_async(request)
        except Exception:
            logger.exception(
                "embedding_failed",
                extra={
                    "provider": "gemini",
                    "model": self.model,
                    "duration_ms": round(
                        (time.perf_counter() - start_time) * 1000,
                        2,
                    ),
                },
            )
            raise