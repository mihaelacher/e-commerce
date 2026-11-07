from typing import Any, ClassVar

from app.ai.clients.embedding_base import EmbeddingClient
from app.ai.tools.schemas import SearchProductsInput
from app.repositories.product.async_product import (
    AsyncProductRepository as ProductRepository,
)


class SearchProductsTool:
    name: ClassVar[str] = "search_products"
    input_model = SearchProductsInput
    requires_confirmation = False

    definition: ClassVar[dict[str, Any]] = {
        "name": name,
        "description": (
            "Search the store's product inventory for product-finding requests. "
            "Treat a first-person statement of need as a request for product "
            "recommendations, even without an explicit 'find' or 'search' command "
            "or a named product category; do not answer only with general advice. "
            "Use the described need or use case as the query. Apply concrete "
            "price limits as min_price or max_price, even when the limit seems "
            "unusually low. Do not guess which products are in the store."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Product category, need, or use case to search for; omit "
                        "price constraints because they belong in min_price or "
                        "max_price."
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
