from typing import ClassVar

from app.ai.clients.embedding_base import EmbeddingClient
from app.ai.tools.schemas import SearchProductsInput
from app.repositories.product.async_product import (
    AsyncProductRepository as ProductRepository,
)


class SearchProductsTool:
    name: ClassVar[str] = "search_products"
    input_model = SearchProductsInput
    requires_confirmation = False

    definition: ClassVar[dict[str, object]] = {
        "name": name,
        "description": (
            "Search the product catalog whenever the customer wants a product, "
            "even if they describe a need indirectly instead of naming a category "
            "(for example, 'something cheap for listening to music'). Put the "
            "described need or use case in query. Pass any stated budget or price "
            "limit as min_price or max_price; do not skip the search because the "
            "budget seems unusually low (for example, 'a laptop under 1' uses "
            "query='laptop' and max_price=1). Also use for product comparisons "
            "and requests to show, list, or browse the catalog."
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
