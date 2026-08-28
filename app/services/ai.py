from turtle import distance

from app.ai.clients.llm_base import LLMClient
from app.ai.clients.embedding_base import EmbeddingClient
from app.ai.clients.product_query_parser import ProductQueryParser
from app.repositories.product import ProductRepository


class AIService:
    def __init__(
        self,
        ai_client: LLMClient,
        embedding_client: EmbeddingClient,
        product_repository: ProductRepository,
        query_parser: ProductQueryParser,
    ) -> None:
        self.ai_client = ai_client
        self.embedding_client = embedding_client
        self.product_repository = product_repository
        self.query_parser = query_parser

    def chat(self, message: str) -> str:
        query = self.query_parser.parse(message)

        query_embedding = self.embedding_client.embed(
            query.search_query
        )

        results = self.product_repository.semantic_search(
            query_embedding=query_embedding,
            min_price=query.min_price,
            max_price=query.max_price,
            limit=5,
        )

        relevant_results = [
            (product, distance)
            for product, distance in results
            if distance < 0.5
        ]

        if not relevant_results:
            return (
                "I couldn't find sufficiently relevant products "
                "matching your requirements."
            )

        context = "\n\n".join(
            (
                f"Product: {product.name}\n"
                f"Price: {product.price} EUR\n"
                f"Stock: {product.stock}\n"
                f"Description: {product.description or ''}"
            )
            for product, distance in relevant_results
        )

        prompt = f"""
            Customer question:
            {message}

            Products matching the customer's requirements:
            {context}

            Answer using only the products above.

            Rules:
            - Do not invent products.
            - Do not invent prices, features, or stock levels.
            - Respect the customer's price requirements.
            - If the available information is insufficient, say so.
            """

        return self.ai_client.chat(prompt)