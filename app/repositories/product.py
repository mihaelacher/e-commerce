from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.product import ProductModel
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[ProductModel]):
    def __init__(self, db: Session):
        super().__init__(ProductModel, db)

    def get_with_lock(
        self,
        product_id: int,
    ) -> ProductModel | None:
        stmt = (
            select(self.model)
            .where(self.model.id == product_id)
            .with_for_update()
        )

        return self.db.scalar(stmt)

    def create(self, data: dict) -> ProductModel:
        product = ProductModel(**data)

        return self.add(product)
    

    def get_available_products(self, limit: int = 20) -> list[ProductModel]:
        stmt = (
            select(ProductModel)
            .where(ProductModel.stock > 0)
            .limit(limit)
        )

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
        stmt = (
            select(ProductModel)
            .where(ProductModel.embedding.is_(None))
            .limit(limit)
        )
        
        return list(self.db.scalars(stmt).all())        


    def semantic_search(
        self,
        query_embedding: list[float],
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        limit: int = 5,
    ):
        distance = ProductModel.embedding.cosine_distance(
            query_embedding
        )

        stmt = (
            select(
                ProductModel,
                distance.label("distance"),
            )
            .where(
                ProductModel.embedding.is_not(None),
                ProductModel.stock > 0,
            )
        )

        if min_price is not None:
            stmt = stmt.where(
                ProductModel.price >= min_price
            )

        if max_price is not None:
            stmt = stmt.where(
                ProductModel.price <= max_price
            )

        stmt = (
            stmt
            .order_by(distance)
            .limit(limit)
        )

        return self.db.execute(stmt).all()