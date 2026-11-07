from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.order import OrderModel
from app.repositories.base import BaseRepository


class BaseOrderRepository(BaseRepository[OrderModel]):
    def _get_with_items_for_update(
        self,
        order_id: int,
    ):
        return (
            select(self.model)
            .options(selectinload(self.model.items))
            .where(self.model.id == order_id)
            .with_for_update()
        )
