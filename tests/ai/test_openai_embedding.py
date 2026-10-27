import pytest

from app.ai.clients.openai.embedding import OpenAIEmbeddingClient
from app.core.config import settings
from app.core.dependencies import ai as ai_dependencies
from app.exceptions.ai import AIProviderUnavailableError


class FakeOpenAIEmbeddings:
    def __init__(self, **kwargs):
        self.options = kwargs

    def embed_query(self, text: str) -> list[float]:
        return [0.1] * 768

    async def aembed_query(self, text: str) -> list[float]:
        return [0.2] * 768


def test_openai_embedding_client_uses_settings(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(settings, "openai_embedding_model", "test-embedding-model")
    monkeypatch.setattr(settings, "embedding_dimensions", 768)
    monkeypatch.setattr(
        "app.ai.clients.openai.embedding.OpenAIEmbeddings",
        FakeOpenAIEmbeddings,
    )

    client = OpenAIEmbeddingClient()

    assert client.model == "test-embedding-model"
    assert client.client.options == {
        "model": "test-embedding-model",
        "dimensions": 768,
        "api_key": "test-key",
        "timeout": settings.ai_client_timeout_ms / 1000,
        "max_retries": settings.ai_provider_max_attempts,
    }
    assert client.embed("query") == [0.1] * 768


@pytest.mark.anyio
async def test_openai_embedding_client_supports_async_embeddings(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(
        "app.ai.clients.openai.embedding.OpenAIEmbeddings",
        FakeOpenAIEmbeddings,
    )

    client = OpenAIEmbeddingClient()

    assert await client.embed_async("query") == [0.2] * 768


def test_openai_embedding_client_requires_api_key(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)

    with pytest.raises(AIProviderUnavailableError, match="OPENAI_API_KEY"):
        OpenAIEmbeddingClient()


def test_embedding_dependency_returns_cached_openai_client(monkeypatch):
    client = object()
    monkeypatch.setattr(
        ai_dependencies,
        "OpenAIEmbeddingClient",
        lambda: client,
    )
    ai_dependencies.get_embedding_client.cache_clear()

    try:
        assert ai_dependencies.get_embedding_client() is client
        assert ai_dependencies.get_embedding_client() is client
    finally:
        ai_dependencies.get_embedding_client.cache_clear()
