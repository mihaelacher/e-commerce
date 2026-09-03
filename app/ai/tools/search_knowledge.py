from typing import ClassVar

from app.ai.clients.embedding_base import EmbeddingClient
from app.ai.tools.schemas import SearchKnowledgeInput
from app.repositories.knowledge.async_knowledge_document import (
    AsyncKnowledgeDocumentRepository as KnowledgeDocumentRepository,
)


class SearchKnowledgeTool:
    name = "search_knowledge"
    input_model = SearchKnowledgeInput
    requires_confirmation = False

    definition: ClassVar[dict[str, object]] = {
        "name": name,
        "description": (
            "Search store policies, FAQs, and product guides for information "
            "relevant to the user's question."
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
