import time

from sqlalchemy.orm import Session

from app.core.database import transaction
from app.core.logging import get_logger
from app.enums.order import OrderStatus
from app.enums.payment_status import PaymentStatus
from app.exceptions.checkout import OrderNotFoundError
from app.exceptions.payment import OrderCannotBePaidError, PaymentNotFoundError
from app.models.order import OrderModel
from app.models.payment import PaymentModel
from app.providers.payment.base import PaymentGateway
from app.repositories.order import OrderRepository
from app.repositories.payment import PaymentRepository
from app.repositories.product import ProductRepository
from app.tasks.order_confirmation import notify_order_created_task, send_order_confirmation_task
from app.tasks.payment import process_payment

logger = get_logger(__name__)


def create_payment(
    db: Session,
    order_id: int,
    idempotency_key: str,
    provider: PaymentGateway,
) -> PaymentModel:
    order_repository = OrderRepository(db)
    payment_repository = PaymentRepository(db)
    start_time = time.perf_counter()

    logger.info(
        "payment_creation_started",
        extra={"order_id": order_id, "provider": provider.type},
    )

    with transaction(db):
        order = order_repository.get_for_update(order_id)

        if order is None:
            raise OrderNotFoundError(order_id)

        existing_payment = payment_repository.get_by_idempotency_key(
            order_id=order_id,
            idempotency_key=idempotency_key,
        )

        if existing_payment is not None:
            logger.info(
                "payment_creation_existing",
                extra={
                    "order_id": order_id,
                    "payment_id": existing_payment.id,
                    "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
                },
            )
            return existing_payment

        if payment_repository.has_successful_payment(order_id):
            raise OrderCannotBePaidError(order_id)

        ensure_order_can_be_paid(order)

        payment = payment_repository.create(
            order_id=order.id,
            amount=order.total,
            provider=provider.type,
            idempotency_key=idempotency_key,
        )

    process_payment.delay(payment.id)

    logger.info(
        "payment_creation_completed",
        extra={
            "order_id": order_id,
            "payment_id": payment.id,
            "provider": provider.type,
            "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
        },
    )

    return payment


def ensure_order_can_be_paid(order: OrderModel) -> None:
    if order.status != OrderStatus.PAYMENT_PENDING:
        raise OrderCannotBePaidError(order.id)


def handle_payment_webhook(
    *,
    db: Session,
    payload: dict,
    provider: PaymentGateway,
) -> PaymentModel:
    start_time = time.perf_counter()
    logger.info(
        "payment_webhook_received",
        extra={
            "provider": provider.type,
            "transaction_id": payload.get("transaction_id"),
        },
    )

    result = provider.parse_webhook(payload)

    payment_repository = PaymentRepository(db)
    order_repository = OrderRepository(db)
    product_repository = ProductRepository(db)

    with transaction(db):
        payment = payment_repository.get_by_transaction_id_for_update(
            result.transaction_id
        )

        if payment is None:
            raise PaymentNotFoundError(
                result.transaction_id
            )

        if payment.status != PaymentStatus.PENDING:
            logger.info(
                "payment_webhook_ignored",
                extra={
                    "payment_id": payment.id,
                    "current_status": payment.status.value,
                    "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
                },
            )
            return payment

        order = order_repository.get_with_items_for_update(payment.order_id)

        if order is None:
            raise OrderNotFoundError(payment.order_id)

        if result.success:
            payment.status = PaymentStatus.PAID
            order.status = OrderStatus.PAID
        else:
            payment.status = PaymentStatus.FAILED

            if order.status == OrderStatus.PAYMENT_PENDING:
                for item in sorted(order.items, key=lambda item: item.product_id):
                    product = product_repository.get_with_lock(item.product_id)

                    if product is not None:
                        product.stock += item.quantity

                order.status = OrderStatus.PENDING

    if result.success:
        send_order_confirmation_task.delay(
            recipient=order.email,
            order_id=order.id,
            total=str(order.total),
        )

        notify_order_created_task.delay(
            order_id=order.id,
            total=str(order.total),
        )

    logger.info(
        "payment_webhook_processed",
        extra={
            "payment_id": payment.id,
            "order_id": order.id,
            "success": result.success,
            "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
        },
    )

    return payment