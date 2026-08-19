from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums.payment_status import PaymentStatus
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
        provider: str,
        idempotency_key: str,
    ) -> PaymentModel:
        payment = PaymentModel(
            order_id=order_id,
            amount=amount,
            provider=provider,
            idempotency_key=idempotency_key,
        )
    
        return self.add(payment)


    def get_by_transaction_id_for_update(
        self,
        transaction_id: str,
    ) -> PaymentModel | None:
        stmt = (
            select(self.model)
            .where(self.model.transaction_id == transaction_id)
            .with_for_update()
        )


        return self.db.scalar(stmt)

    def get_by_id(
        self,
        payment_id: int,
    ) -> PaymentModel | None:
        return self.get(payment_id)


    def has_successful_payment(self, order_id: int) -> bool:
        return (
            self.db.query(PaymentModel)
            .filter(
                PaymentModel.order_id == order_id,
                PaymentModel.status ==  PaymentStatus.PAID,
            )
            .first()
        )

    def claim_for_processing(
        self,
        payment_id: int,
        processing_timeout: timedelta,
    ) -> bool:
        now = datetime.now(timezone.utc)
        threshold = now - processing_timeout

        updated = (
            self.db.query(PaymentModel)
            .filter(
                PaymentModel.id == payment_id,
                PaymentModel.status == PaymentStatus.PENDING,
                    (
                        PaymentModel.processing_started_at.is_(None)
                        | (
                            PaymentModel.processing_started_at < threshold
                        )
                    ),
            )
            .update(
                {
                    PaymentModel.processing_started_at: now,
                },
                synchronize_session=False,
            )
        )
    
        self.db.commit()
    
        return updated == 1 