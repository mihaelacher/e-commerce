from sqlalchemy.orm import Session

from app.core.database import transaction
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
from app.tasks.payment import process_payment


def create_payment(
    db: Session,
    order_id: int,
    idempotency_key: str,
    provider: PaymentGateway,
) -> PaymentModel:
    order_repository = OrderRepository(db)
    payment_repository = PaymentRepository(db)

    with transaction(db):
        order = order_repository.get_for_update(order_id)

        if order is None:
            raise OrderNotFoundError(order_id)

        existing_payment = payment_repository.get_by_idempotency_key(
            order_id=order_id,
            idempotency_key=idempotency_key,
        )

        if existing_payment is not None:
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

    return payment