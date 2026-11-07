from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.knowledge_chunk import KnowledgeChunkModel
from app.models.knowledge_document import KnowledgeDocumentModel
from app.repositories.base import BaseRepository


class AsyncKnowledgeDocumentRepository(BaseRepository[KnowledgeDocumentModel]):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def semantic_search(
        self,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[tuple[KnowledgeChunkModel, float]]:
        distance = KnowledgeChunkModel.embedding.cosine_distance(query_embedding).label(
            "distance"
        )

        stmt = (
            select(KnowledgeChunkModel, distance)
            .options(selectinload(KnowledgeChunkModel.document))
            .order_by(distance)
            .limit(limit)
        )

        result = await self.db.execute(stmt)

        return list(result.all())
