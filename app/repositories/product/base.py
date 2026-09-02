from sqlalchemy import select

from app.models.product import ProductModel
from app.repositories.base import BaseRepository


class BaseProductRepository(BaseRepository[ProductModel]):
    def _semantic_search_stmt(
        self,
        query_embedding: list[float],
        min_price: float | None = None,
        max_price: float | None = None,
        limit: int = 5,
    ):
        distance = ProductModel.embedding.cosine_distance(query_embedding).label(
            "distance"
        )

        stmt = select(
            ProductModel,
            distance,
        )

        if min_price is not None:
            stmt = stmt.where(ProductModel.price >= min_price)

        if max_price is not None:
            stmt = stmt.where(ProductModel.price <= max_price)

        return stmt.order_by(distance).limit(limit)
