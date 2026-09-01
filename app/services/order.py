
from sqlalchemy.orm import Session

from app.core.database import transaction
from app.enums.order import OrderStatus
from app.exceptions.checkout import OrderNotFoundError
from app.exceptions.order import (
    OrderCannotBeCancelledError,
    PaidOrderPaymentNotFoundError,
)
from app.models.order import OrderModel
from app.repositories.order import OrderRepository
from app.repositories.payment import PaymentRepository
from app.tasks.refund_payment import refund_order_payment


def get_order(
    db: Session,
    order_id: int,
) -> OrderModel:
    repository = OrderRepository(db)

    order = repository.get(order_id)

    if order is None:
        raise OrderNotFoundError(order_id)

    return order


def cancel_order(
    db: Session,
    order_id: int,
) -> OrderModel:
    with transaction(db):
        order_repository = OrderRepository(db)
        payment_repository = PaymentRepository(db)

        order = order_repository.get_with_items_for_update(
            order_id
        )

        if order is None:
            raise OrderNotFoundError(order_id)

        if order.status in (OrderStatus.CANCELLED, OrderStatus.CANCELLATION_PENDING):
            return order

        if order.status in (OrderStatus.PENDING, OrderStatus.PAYMENT_PENDING):
            raise OrderCannotBeCancelledError(
                order_id=order.id,
                status=order.status,
            )

        if order.status == OrderStatus.COMPLETED:
            order.status = OrderStatus.CANCELLED

        elif order.status == OrderStatus.PAID:
            payment = payment_repository.get_paid_by_order_id_for_update(
                order.id
            )

            if payment is None:
                raise PaidOrderPaymentNotFoundError(order.id)

            order.status = OrderStatus.CANCELLATION_PENDING
            payment = payment_repository.get(order.payment_id)
        
        db.flush()

        refund_order_payment.delay(order.id)

        return order