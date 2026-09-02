from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.order import OrderModel
from app.repositories.order.base import BaseOrderRepository


class OrderRepository(BaseOrderRepository):
    def __init__(self, db: Session):
        super().__init__(OrderModel, db)

    def get_with_items(
        self,
        order_id: int,
    ) -> OrderModel | None:
        stmt = (
            select(self.model)
            .options(selectinload(self.model.items))
            .where(self.model.id == order_id)
        )

        return self.db.scalar(stmt)

    def create(
        self,
        email: str,
    ) -> OrderModel:
        order = OrderModel(email=email)

        return self.add(order)

    def get_with_items_for_update(
        self,
        order_id: int,
    ) -> OrderModel | None:
        stmt = self._get_with_items_for_update(order_id)

        return self.db.scalar(stmt)

    def get_for_update(
        self,
        order_id: int,
    ) -> OrderModel | None:
        stmt = select(self.model).where(self.model.id == order_id).with_for_update()

        return self.db.scalar(stmt)
