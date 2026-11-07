from types import SimpleNamespace

import pytest

from app.ai.tools.search_products import SearchProductsTool


class FakeEmbeddingClient:
    async def embed_async(self, text: str):
        return [0.1, 0.2, 0.3]


class FakeProductRepository:
    async def semantic_search(
        self,
        query_embedding,
        min_price=None,
        max_price=None,
        limit=5,
    ):
        product = SimpleNamespace(
            id=1,
            name="Quiet Headphones",
            price=99.99,
            stock=3,
            description="Noise cancelling",
        )

        return [
            (product, 0.2),
        ]


class EmptyProductRepository:
    async def semantic_search(
        self,
        query_embedding,
        min_price=None,
        max_price=None,
        limit=5,
    ):
        return []


@pytest.mark.anyio
async def test_search_products():
    tool = SearchProductsTool(
        embedding_client=FakeEmbeddingClient(),
        product_repository=FakeProductRepository(),
    )

    result = await tool.execute(
        query="wireless headphones",
        max_price=150,
    )

    assert result == [
        {
            "name": "Quiet Headphones",
            "price": "99.99",
            "stock": 3,
            "description": "Noise cancelling",
        }
    ]


@pytest.mark.anyio
async def test_search_products_returns_empty_list_when_no_results():
    tool = SearchProductsTool(
        embedding_client=FakeEmbeddingClient(),
        product_repository=EmptyProductRepository(),
    )

    result = await tool.execute(
        query="wireless headphones",
    )

    assert result == []
