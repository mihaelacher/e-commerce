from datetime import timedelta

from app.core.database import SessionLocal
from app.core.dependencies.payment import get_payment_provider
from app.core.logging import capture_exception, get_logger
from app.enums.payment_status import PaymentStatus
from app.repositories.payment import PaymentRepository
from app.tasks.celery import celery_app

logger = get_logger(__name__)


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

    logger.info(
        "payment_task_started",
        extra={
            "payment_id": payment_id,
            "provider": "payment_provider",
        },
    )

    try:
        claimed = payment_repository.claim_for_processing(
            payment_id,
            processing_timeout=timedelta(minutes=5),
        )

        if not claimed:
            logger.info(
                "payment_task_already_claimed",
                extra={
                    "payment_id": payment_id,
                    "provider": "payment_provider",
                },
            )
            return

        payment = payment_repository.get_by_id(payment_id)

        if payment is None:
            logger.warning(
                "payment_task_missing_payment",
                extra={
                    "payment_id": payment_id,
                    "provider": "payment_provider",
                },
            )
            return

        provider = get_payment_provider()
        provider_name = type(provider).__name__

        result = provider.charge(
            amount=payment.amount,
            idempotency_key=payment.idempotency_key,
        )

        payment.transaction_id = result.transaction_id
        db.commit()
        logger.info(
            "payment_task_completed",
            extra={
                "payment_id": payment_id,
                "provider": provider_name,
                "transaction_id": result.transaction_id,
            },
        )

    except Exception as exc:
        db.rollback()

        payment = payment_repository.get_by_id(payment_id)
        if payment is not None and payment.status == PaymentStatus.PENDING:
            payment.processing_started_at = None
            db.commit()

        logger.exception(
            "payment_task_failed",
            extra={
                "payment_id": payment_id,
                "provider": "payment_provider",
            },
        )
        capture_exception(exc, payment_id=payment_id)
        raise

    finally:
        db.close()