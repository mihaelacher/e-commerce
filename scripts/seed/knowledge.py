import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chunking import chunk_text
from app.ai.clients.embedding_base import EmbeddingClient
from app.core.database import AsyncSessionLocal
from app.core.dependencies.ai import get_embedding_client
from app.enums.knowledge_document import KnowledgeDocumentType
from app.models.knowledge_chunk import KnowledgeChunkModel
from app.models.knowledge_document import KnowledgeDocumentModel

KNOWLEDGE_DOCUMENTS = [
    {
        "title": "Returns Policy",
        "source": "internal_policy",
        "document_type": KnowledgeDocumentType.POLICY,
        "content": """
            Customers may return eligible products within 30 days of delivery.

            Products must be returned in their original condition. Items that are damaged
            through misuse may not qualify for a full refund.

            Opened products may be returned unless the item belongs to a category excluded
            for hygiene or safety reasons.

            Refunds are issued after the returned product has been received and inspected.
        """.strip(),
    },
    {
        "title": "Shipping Policy",
        "source": "internal_policy",
        "document_type": KnowledgeDocumentType.POLICY,
        "content": """
            Orders are normally processed within one business day.

            Standard shipping usually takes 3 to 5 business days after dispatch.

            Delivery times may be longer during holidays, high-volume periods, or when
            shipping to remote locations.

            Customers receive tracking information when an order has been dispatched.
        """.strip(),
    },
    {
        "title": "Refund Policy",
        "source": "internal_policy",
        "document_type": KnowledgeDocumentType.POLICY,
        "content": """
            Approved refunds are returned to the original payment method.

            Refund processing normally begins after a returned product has been inspected.

            Banks and payment providers may require additional time before the refunded
            amount appears in the customer's account.

            Shipping charges are refundable only when required by the applicable return
            conditions or when the order was incorrect or defective.
        """.strip(),
    },
    {
        "title": "Warranty Policy",
        "source": "internal_policy",
        "document_type": KnowledgeDocumentType.POLICY,
        "content": """
            Products may include a manufacturer warranty.

            Warranty coverage applies to manufacturing defects and does not normally cover
            accidental damage, misuse, or normal wear.

            Customers should provide their order information when requesting warranty
            support.
        """.strip(),
    },
    {
        "title": "Store FAQ",
        "source": "internal_faq",
        "document_type": KnowledgeDocumentType.FAQ,
        "content": """
            Customers can check the status of an existing order using their order number.

            Orders that have already been paid may require a refund process when cancelled.

            Customers can search the catalog by product type, price range, and other
            available product information.
        """.strip(),
    },
]


async def create_chunks_for_document(
    db: AsyncSession,
    document: KnowledgeDocumentModel,
    embedding_client: EmbeddingClient,
) -> None:
    chunks = chunk_text(document.content)

    for index, content in enumerate(chunks):
        embedding = await embedding_client.embed_async(content)

        db.add(
            KnowledgeChunkModel(
                document_id=document.id,
                content=content,
                chunk_index=index,
                embedding=embedding,
            )
        )


async def seed_knowledge_documents(
    db: AsyncSession,
    embedding_client: EmbeddingClient,
) -> None:
    for data in KNOWLEDGE_DOCUMENTS:
        stmt = select(KnowledgeDocumentModel).where(
            KnowledgeDocumentModel.title == data["title"],
            KnowledgeDocumentModel.source == data["source"],
        )

        result = await db.execute(stmt)
        existing_document = result.scalar_one_or_none()

        if existing_document is not None:
            continue

        document = KnowledgeDocumentModel(
            title=data["title"],
            source=data["source"],
            document_type=data["document_type"],
            content=data["content"],
        )

        db.add(document)

        await db.flush()

        await create_chunks_for_document(
            db=db,
            document=document,
            embedding_client=embedding_client,
        )

    await db.commit()


async def main() -> None:
    async with AsyncSessionLocal() as db:
        embedding_client = get_embedding_client()

        await seed_knowledge_documents(
            db=db,
            embedding_client=embedding_client,
        )


if __name__ == "__main__":
    asyncio.run(main())
