from sqlalchemy.orm import Session

from app.core.database import transaction
from app.enums.order import OrderStatus
from app.enums.payment_provider import PaymentProvider
from app.enums.payment_status import PaymentStatus
from app.exceptions.checkout import OrderNotFoundError
from app.exceptions.payment import OrderCannotBePaidError
from app.models.order import OrderModel
from app.models.payment import PaymentModel
from app.providers.payment.base import PaymentGateway
from app.repositories.order import OrderRepository
from app.repositories.payment import PaymentRepository


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

        ensure_order_can_be_paid(order)

        payment = payment_repository.create(
            order_id=order.id,
            amount=order.total,
            provider=PaymentProvider.MOCK,
            idempotency_key=idempotency_key,
        )

        result = provider.charge(
            amount=payment.amount,
            idempotency_key=idempotency_key,
        )

        if result.success:
            payment.status = PaymentStatus.PAID
            payment.transaction_id = result.transaction_id
            order.status = OrderStatus.PAID
        else:
            payment.status = PaymentStatus.FAILED

        return payment


def ensure_order_can_be_paid(order: OrderModel) -> None:
    if order.status != OrderStatus.PAYMENT_PENDING:
        raise OrderCannotBePaidError(order.id)