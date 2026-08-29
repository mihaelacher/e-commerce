from datetime import timedelta

from app.core.database import SessionLocal
from app.core.dependencies.payment import get_payment_provider
from app.enums.payment_status import PaymentStatus
from app.repositories.payment import PaymentRepository
from app.tasks.celery import celery_app


@celery_app.task(
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_backoff_max=300,
    retry_jitter=False,
    max_retries=3,
)
def process_payment(payment_id: int) -> None:
    db = SessionLocal()
    payment_repository = PaymentRepository(db)

    try:
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

    except Exception:
        db.rollback()

        payment = payment_repository.get_by_id(payment_id)
        if payment is not None and payment.status == PaymentStatus.PENDING:
            payment.processing_started_at = None
            db.commit()

        raise

    finally:
        db.close()