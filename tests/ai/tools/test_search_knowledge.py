from types import SimpleNamespace

import pytest

from app.ai.tools.search_knowledge import SearchKnowledgeTool


class FakeEmbeddingClient:
    async def embed_async(self, text: str) -> list[float]:
        assert text == "How many days do I have to return a product?"

        return [0.1, 0.2, 0.3]


class FakeKnowledgeRepository:
    async def semantic_search(
        self,
        query_embedding: list[float],
        limit: int = 5,
    ):
        assert query_embedding == [0.1, 0.2, 0.3]
        assert limit == 5

        document = SimpleNamespace(
            title="Returns Policy",
            source="internal_policy",
            document_type=SimpleNamespace(value="policy"),
        )

        chunk = SimpleNamespace(
            content=(
                "Customers may return eligible products within 30 days of delivery."
            ),
            document=document,
        )

        return [
            (
                chunk,
                0.18,
            )
        ]


class MultipleResultsKnowledgeRepository(FakeKnowledgeRepository):
    async def semantic_search(
        self,
        query_embedding: list[float],
        limit: int = 5,
    ):
        results = await super().semantic_search(query_embedding, limit)
        return [*results, (results[0][0], 0.5)]


@pytest.mark.asyncio
async def test_search_knowledge_returns_relevant_chunks():
    tool = SearchKnowledgeTool(
        repository=FakeKnowledgeRepository(),
        embedding_client=FakeEmbeddingClient(),
    )

    result = await tool.execute(query="How many days do I have to return a product?")

    assert result == [
        {
            "title": "Returns Policy",
            "source": "internal_policy",
            "document_type": "policy",
            "content": (
                "Customers may return eligible products within 30 days of delivery."
            ),
            "distance": 0.18,
        }
    ]


@pytest.mark.asyncio
async def test_search_knowledge_excludes_irrelevant_chunks():
    tool = SearchKnowledgeTool(
        repository=MultipleResultsKnowledgeRepository(),
        embedding_client=FakeEmbeddingClient(),
    )

    result = await tool.execute(query="How many days do I have to return a product?")

    assert len(result) == 1
    assert result[0]["distance"] == 0.18
