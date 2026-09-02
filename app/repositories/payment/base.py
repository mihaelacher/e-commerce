from sqlalchemy import select

from app.enums.payment_status import PaymentStatus
from app.models.payment import PaymentModel
from app.repositories.base import BaseRepository


class BasePaymentRepository(BaseRepository[PaymentModel]):
    def _get_paid_by_order_id_for_update(
        self,
        order_id: int,
    ):
        return (
            select(self.model)
            .where(self.model.order_id == order_id)
            .where(self.model.status == PaymentStatus.PAID)
            .with_for_update()
        )
