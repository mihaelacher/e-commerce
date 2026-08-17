from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums.payment_provider import PaymentProvider
from app.models.payment import PaymentModel
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[PaymentModel]):
    def __init__(self, db: Session):
        super().__init__(PaymentModel, db)

    def get_by_idempotency_key(
        self,
        order_id: int,
        idempotency_key: str,
    ) -> PaymentModel | None:
        stmt = (
            select(self.model)
            .where(self.model.idempotency_key == idempotency_key)
            .where(self.model.order_id == order_id)
        )

        return self.db.scalar(stmt)
    
    def create(
        self,
        order_id: int,
        amount: Decimal,
        provider: PaymentProvider,
        idempotency_key: str,
    ) -> PaymentModel:
        payment = PaymentModel(
            order_id=order_id,
            amount=amount,
            provider=provider,
            idempotency_key=idempotency_key,
        )
    
        return self.add(payment)
    