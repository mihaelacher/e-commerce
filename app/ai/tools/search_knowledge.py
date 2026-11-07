from typing import Any, ClassVar

from app.ai.clients.embedding_base import EmbeddingClient
from app.ai.tools.schemas import SearchKnowledgeInput
from app.repositories.knowledge.async_knowledge_document import (
    AsyncKnowledgeDocumentRepository as KnowledgeDocumentRepository,
)


class SearchKnowledgeTool:
    name = "search_knowledge"
    input_model = SearchKnowledgeInput
    requires_confirmation = False

    definition: ClassVar[dict[str, Any]] = {
        "name": name,
        "description": (
            "Retrieve relevant passages from store policies, FAQs, and product "
            "guides. Use for questions about rules, terms, or eligibility, "
            "including whether an action is allowed. When eligibility depends "
            "on a specific order, use this together with get_order_status: this "
            "tool provides policy information but does not check order status "
            "or perform actions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": ("The question or information to search for."),
                },
            },
            "required": ["query"],
        },
    }

    def __init__(
        self,
        repository: KnowledgeDocumentRepository,
        embedding_client: EmbeddingClient,
    ):
        self.repository = repository
        self.embedding_client = embedding_client

    async def execute(
        self,
        query: str,
    ) -> list[dict]:
        query_embedding = await self.embedding_client.embed_async(query)

        results = await self.repository.semantic_search(
            query_embedding=query_embedding,
            limit=5,
        )

        return [
            {
                "title": chunk.document.title,
                "source": chunk.document.source,
                "document_type": chunk.document.document_type.value,
                "content": chunk.content,
                "distance": float(distance),
            }
            for chunk, distance in results
            if distance < 0.5
        ]
