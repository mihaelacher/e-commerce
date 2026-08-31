import time

from google import genai
from google.genai import types

from app.ai.clients.embedding_base import EmbeddingClient
from app.ai.clients.gemini.helper import with_retry
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiEmbeddingClient(EmbeddingClient):
    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.gemini_api_key,
        )

    def embed(self, text: str) -> list[float]:
        start_time = time.perf_counter()

        def request():
            response = self.client.models.embed_content(
                model="gemini-embedding-2",
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
                    "model": "gemini-embedding-2",
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
                    "model": "gemini-embedding-2",
                    "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
                },
            )
            raise