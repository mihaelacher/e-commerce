from typing import ClassVar

from app.ai.clients.embedding_base import EmbeddingClient
from app.ai.tools.schemas import SearchProductsInput
from app.repositories.product.async_product import AsyncProductRepository as ProductRepository


class SearchProductsTool:
    name: ClassVar[str] = "search_products"
    input_model = SearchProductsInput
    requires_confirmation = False

    definition: ClassVar[dict[str, object]] = {
        "name": name,
        "description": "Search available products matching the customer's request.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The semantic product search query without price constraints."
                    ),
                },
                "min_price": {
                    "type": "number",
                    "description": "Minimum product price, if specified.",
                },
                "max_price": {
                    "type": "number",
                    "description": "Maximum product price, if specified.",
                },
            },
            "required": ["query"],
        },
    }

    def __init__(
        self,
        embedding_client: EmbeddingClient,
        product_repository: ProductRepository,
    ):
        self.embedding_client = embedding_client
        self.product_repository = product_repository

    async def execute(
        self,
        query: str,
        min_price: float | None = None,
        max_price: float | None = None,
    ) -> list[dict]:
        query_embedding = await self.embedding_client.embed_async(query)

        results = await self.product_repository.semantic_search(
            query_embedding=query_embedding,
            min_price=min_price,
            max_price=max_price,
            limit=5,
        )

        return [
            {
                "name": product.name,
                "price": str(product.price),
                "stock": product.stock,
                "description": product.description,
            }
            for product, distance in results
            if distance < 0.5
        ]