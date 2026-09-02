from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.product import ProductModel
from app.repositories.product.base import BaseProductRepository


class ProductRepository(BaseProductRepository):
    def __init__(self, db: Session):
        super().__init__(ProductModel, db)

    def get_with_lock(
        self,
        product_id: int,
    ) -> ProductModel | None:
        stmt = select(self.model).where(self.model.id == product_id).with_for_update()

        return self.db.scalar(stmt)

    def create(self, data: dict) -> ProductModel:
        product = ProductModel(**data)

        return self.add(product)

    def get_available_products(self, limit: int = 20) -> list[ProductModel]:
        stmt = select(ProductModel).where(ProductModel.stock > 0).limit(limit)

        return list(self.db.scalars(stmt).all())

    def search_available(
        self,
        query: str,
        limit: int = 10,
    ) -> list[ProductModel]:
        search = f"%{query}%"

        stmt = (
            select(ProductModel)
            .where(
                ProductModel.stock > 0,
                or_(
                    ProductModel.name.ilike(search),
                    ProductModel.description.ilike(search),
                ),
            )
            .limit(limit)
        )

        return list(self.db.scalars(stmt).all())

    def get_without_embedding(
        self,
        limit: int = 100,
    ) -> list[ProductModel]:
        stmt = select(ProductModel).where(ProductModel.embedding.is_(None)).limit(limit)

        return list(self.db.scalars(stmt).all())

    def semantic_search(
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

        return self.db.execute(stmt).all()
