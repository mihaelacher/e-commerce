from datetime import timedelta

from app.core.database import SessionLocal
from app.core.dependencies import get_payment_provider
from app.enums.payment_status import PaymentStatus
from app.repositories.payment import PaymentRepository
from app.tasks.celery import celery_app


@celery_app.task
def process_payment(payment_id: int) -> None:
    db = SessionLocal()

    try:
        payment_repository = PaymentRepository(db)

        claimed = payment_repository.claim_for_processing(
            payment_id,
            processing_timeout=timedelta(minutes=5),
        )

        if not claimed:
            return

        payment = payment_repository.get_by_id(payment_id)

        if payment is None:
            return

        provider = get_payment_provider()

        result = provider.charge(
            amount=payment.amount,
            idempotency_key=payment.idempotency_key,
        )

        payment.transaction_id = result.transaction_id
        db.commit()

    finally:
        db.close()