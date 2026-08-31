from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, update
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
        stmt = (
            select(self.model.id)
            .where(
                self.model.order_id == order_id,
                self.model.status == PaymentStatus.PAID,
            )
            .limit(1)
        )

        return self.db.scalar(stmt) is not None

    def claim_for_processing(
        self,
        payment_id: int,
        processing_timeout: timedelta,
    ) -> bool:
        now = datetime.now(UTC)
        threshold = now - processing_timeout    

        stmt = (
            update(self.model)
            .where(
                self.model.id == payment_id,
                self.model.status == PaymentStatus.PENDING,
                (
                    self.model.processing_started_at.is_(None)
                    | (self.model.processing_started_at < threshold)
                ),
            )
            .values(processing_started_at=now)
        )   

        result = self.db.execute(stmt)
        self.db.commit()    

        return result.rowcount == 1