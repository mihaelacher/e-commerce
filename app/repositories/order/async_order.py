from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import OrderModel
from app.repositories.order.base import BaseOrderRepository


class AsyncOrderRepository(BaseOrderRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(OrderModel, db)

    async def get(
        self,
        order_id: int,
    ) -> OrderModel | None:
        stmt = select(OrderModel).where(OrderModel.id == order_id)

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_with_items_for_update(
        self,
        order_id: int,
    ) -> OrderModel | None:
        stmt = self._get_with_items_for_update(order_id)

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()
