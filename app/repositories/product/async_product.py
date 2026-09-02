from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.product.base import BaseProductRepository


class AsyncProductRepository(BaseProductRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def semantic_search(
        self,
        query_embedding: list[float],
        min_price: float | None = None,
        max_price: float | None = None,
        limit: int = 5,
    ):
        stmt = self._semantic_search_stmt(
            query_embedding=query_embedding,
            min_price=min_price,
            max_price=max_price,
            limit=limit,
        )

        result = await self.db.execute(stmt)

        return result.all()