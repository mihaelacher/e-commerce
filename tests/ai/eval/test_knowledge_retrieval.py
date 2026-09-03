import pytest

from app.ai.chunking import chunk_text
from app.core.dependencies.ai import get_embedding_client
from app.enums.knowledge_document import KnowledgeDocumentType
from app.models.knowledge_chunk import KnowledgeChunkModel
from app.models.knowledge_document import KnowledgeDocumentModel
from app.repositories.knowledge.async_knowledge_document import (
    AsyncKnowledgeDocumentRepository as KnowledgeDocumentRepository,
)


@pytest.mark.asyncio
async def test_semantic_search_returns_relevant_chunks(
    async_db,
):
    embedding_client = get_embedding_client()

    document = KnowledgeDocumentModel(
        title="Returns Policy",
        source="internal_policy",
        document_type=KnowledgeDocumentType.POLICY,
        content="""
            Customers may return eligible products within 30 days of delivery.

            Products must be returned in their original condition.

            Opened products may be returned unless the item belongs to a category
            excluded for hygiene or safety reasons.
        """.strip(),
    )

    async_db.add(document)
    await async_db.flush()

    chunks = chunk_text(document.content)

    for index, content in enumerate(chunks):
        embedding = await embedding_client.embed_async(content)

        async_db.add(
            KnowledgeChunkModel(
                document_id=document.id,
                content=content,
                chunk_index=index,
                embedding=embedding,
            )
        )

    await async_db.flush()

    query_embedding = await embedding_client.embed_async(
        "How many days do I have to return a product?"
    )

    repository = KnowledgeDocumentRepository(async_db)

    results = await repository.semantic_search(
        query_embedding=query_embedding,
        limit=5,
    )

    assert results

    for chunk, distance in results:
        print()
        print(f"Document: {chunk.document.title}")
        print(f"Distance: {distance}")
        print(f"Content: {chunk.content}")

    top_chunk, _ = results[0]

    assert top_chunk.document.title == "Returns Policy"
