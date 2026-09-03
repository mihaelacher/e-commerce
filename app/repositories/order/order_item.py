from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order import OrderModel
from app.models.order_item import OrderItemModel
from app.repositories.base import BaseRepository


class OrderItemRepository(BaseRepository[OrderItemModel]):
    def __init__(self, db: Session):
        super().__init__(OrderItemModel, db)

    def create(
        self,
        *,
        order: OrderModel,
        product_id: int,
        quantity: int,
        unit_price: Decimal,
    ) -> OrderItemModel:
        item = OrderItemModel(
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            total_price=unit_price * quantity,
        )
        order.items.append(item)
        return self.add(item)

    def get_by_order_and_product(
        self,
        *,
        order_id: int,
        product_id: int,
    ) -> OrderItemModel | None:
        stmt = select(self.model).where(
            self.model.order_id == order_id,
            self.model.product_id == product_id,
        )

        return self.db.scalar(stmt)
