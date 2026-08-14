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
        return (
            self.db.query(self.model)
            .filter(self.model.id == product_id)
            .with_for_update()
            .first()
        )

    def create(self, data: dict) -> ProductModel:
        product = ProductModel(**data)

        return self.add(product)
