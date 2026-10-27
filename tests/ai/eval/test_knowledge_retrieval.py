import pytest
from langgraph.checkpoint.memory import InMemorySaver

from app.ai.chunking import chunk_text
from app.ai.clients.openai.langchain_client import LangChainClient
from app.ai.tools.cancel_order import CancelOrderTool
from app.ai.tools.get_order_status import GetOrderStatusTool
from app.ai.tools.search_knowledge import SearchKnowledgeTool
from app.ai.tools.search_products import SearchProductsTool
from app.core.dependencies.ai import get_embedding_client
from app.enums.knowledge_document import KnowledgeDocumentType
from app.models.knowledge_chunk import KnowledgeChunkModel
from app.models.knowledge_document import KnowledgeDocumentModel
from app.repositories.knowledge.async_knowledge_document import (
    AsyncKnowledgeDocumentRepository as KnowledgeDocumentRepository,
)
from app.repositories.order.async_order import AsyncOrderRepository
from app.repositories.product.async_product import AsyncProductRepository
from app.services.ai.langgraph_ai import LangGraphAIService


def add_document(db, title: str, content: str) -> KnowledgeDocumentModel:
    document = KnowledgeDocumentModel(
        title=title,
        source="eval_fixture",
        document_type=KnowledgeDocumentType.POLICY,
        content=content,
    )
    db.add(document)
    return document


@pytest.mark.eval
@pytest.mark.asyncio
async def test_semantic_search_returns_relevant_chunks(
    async_db,
):
    embedding_client = get_embedding_client()

    document = add_document(
        async_db,
        title="Returns Policy",
        content="""
            Customers may return eligible products within 30 days of delivery.

            Products must be returned in their original condition.

            Opened products may be returned unless the item belongs to a category
            excluded for hygiene or safety reasons.
        """.strip(),
    )
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
    assert "30 days" in top_chunk.content


@pytest.mark.eval
@pytest.mark.asyncio
async def test_rag_answer_uses_retrieved_policy_fact(async_db):
    embedding_client = get_embedding_client()
    document = add_document(
        async_db,
        title="Returns Policy",
        content="Customers may return eligible products within 30 days of delivery.",
    )
    await async_db.flush()

    async_db.add(
        KnowledgeChunkModel(
            document_id=document.id,
            content=document.content,
            chunk_index=0,
            embedding=await embedding_client.embed_async(document.content),
        )
    )
    await async_db.flush()

    search_knowledge_tool = SearchKnowledgeTool(
        repository=KnowledgeDocumentRepository(async_db),
        embedding_client=embedding_client,
    )
    service = LangGraphAIService(
        llm=LangChainClient().get_client(),
        search_products_tool=SearchProductsTool(
            embedding_client=embedding_client,
            product_repository=AsyncProductRepository(async_db),
        ),
        search_knowledge_tool=search_knowledge_tool,
        get_order_status_tool=GetOrderStatusTool(
            order_repository=AsyncOrderRepository(async_db),
        ),
        cancel_order_tool=CancelOrderTool(db=async_db),
        checkpointer=InMemorySaver(),
    )

    response = await service.chat(
        message=(
            "According to the store's returns policy, how long do I have to "
            "return an eligible product?"
        ),
        conversation_id="returns-policy-eval",
    )

    normalized_answer = response.answer.lower()
    assert "30" in normalized_answer
    assert "day" in normalized_answer
