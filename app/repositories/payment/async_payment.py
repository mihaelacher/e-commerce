from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import PaymentModel
from app.repositories.payment.base import BasePaymentRepository


class AsyncPaymentRepository(BasePaymentRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(PaymentModel, db)

    async def get_paid_by_order_id_for_update(
        self,
        order_id: int,
    ) -> PaymentModel | None:
        stmt = self._get_paid_by_order_id_for_update(order_id)

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()
