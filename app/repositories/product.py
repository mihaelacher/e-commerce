from sqlalchemy import select
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