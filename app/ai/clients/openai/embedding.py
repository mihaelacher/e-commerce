from time import perf_counter

from langchain_openai import OpenAIEmbeddings

from app.ai.clients.embedding_base import EmbeddingClient
from app.core.config import settings
from app.core.logging import get_logger
from app.exceptions.ai import AIProviderUnavailableError

logger = get_logger(__name__)


class OpenAIEmbeddingClient(EmbeddingClient):
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise AIProviderUnavailableError(
                "OPENAI_API_KEY must be configured to use OpenAI embeddings."
            )

        self.model = settings.openai_embedding_model
        self.client = OpenAIEmbeddings(
            model=self.model,
            dimensions=settings.embedding_dimensions,
            api_key=settings.openai_api_key,
            timeout=settings.ai_client_timeout_ms / 1000,
            max_retries=settings.ai_provider_max_attempts,
        )

    def embed(self, text: str) -> list[float]:
        start_time = perf_counter()

        try:
            embedding = self.client.embed_query(text)
        except Exception:
            logger.exception(
                "embedding_failed",
                extra={
                    "provider": "openai",
                    "model": self.model,
                    "operation": "embed",
                    "duration_ms": round((perf_counter() - start_time) * 1000, 2),
                },
            )
            raise

        logger.info(
            "embedding_completed",
            extra={
                "provider": "openai",
                "model": self.model,
                "operation": "embed",
                "duration_ms": round((perf_counter() - start_time) * 1000, 2),
            },
        )
        return embedding

    async def embed_async(self, text: str) -> list[float]:
        start_time = perf_counter()

        try:
            embedding = await self.client.aembed_query(text)
        except Exception:
            logger.exception(
                "embedding_failed",
                extra={
                    "provider": "openai",
                    "model": self.model,
                    "operation": "embed_async",
                    "duration_ms": round((perf_counter() - start_time) * 1000, 2),
                },
            )
            raise

        logger.info(
            "embedding_completed",
            extra={
                "provider": "openai",
                "model": self.model,
                "operation": "embed_async",
                "duration_ms": round((perf_counter() - start_time) * 1000, 2),
            },
        )
        return embedding
