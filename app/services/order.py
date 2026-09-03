from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.database import transaction
from app.enums.order import OrderStatus
from app.enums.payment_status import PaymentStatus
from app.exceptions.checkout import OrderNotFoundError
from app.exceptions.order import (
    OrderCannotBeCancelledError,
    PaidOrderPaymentNotFoundError,
)
from app.models.order import OrderModel
from app.repositories.order.async_order import AsyncOrderRepository
from app.repositories.order.sync_order import OrderRepository
from app.repositories.payment.async_payment import AsyncPaymentRepository
from app.repositories.payment.sync_payment import PaymentRepository
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
    requires_refund = False

    with transaction(db):
        order_repository = OrderRepository(db)
        payment_repository = PaymentRepository(db)

        order = order_repository.get_with_items_for_update(order_id)

        if order is None:
            raise OrderNotFoundError(order_id)

        if order.status in (
            OrderStatus.CANCELLED,
            OrderStatus.CANCELLATION_PENDING,
        ):
            return order

        if order.status in (
            OrderStatus.PENDING,
            OrderStatus.PAYMENT_PENDING,
        ):
            raise OrderCannotBeCancelledError(
                order_id=order.id,
                status=order.status,
            )

        if order.status == OrderStatus.COMPLETED:
            order.status = OrderStatus.CANCELLED

        elif order.status == OrderStatus.PAID:
            payment = payment_repository.get_paid_by_order_id_for_update(order.id)

            if payment is None:
                raise PaidOrderPaymentNotFoundError(order.id)

            order.status = OrderStatus.CANCELLATION_PENDING
            payment.status = PaymentStatus.REFUND_PENDING

            requires_refund = True

        db.flush()

    if requires_refund:
        refund_order_payment.delay(order.id)

    return order


async def cancel_order_async(
    db: AsyncSession,
    order_id: int,
) -> OrderModel:
    requires_refund = False

    async with db.begin():
        order_repository = AsyncOrderRepository(db)
        payment_repository = AsyncPaymentRepository(db)

        order = await order_repository.get_with_items_for_update(order_id)

        if order is None:
            raise OrderNotFoundError(order_id)

        if order.status in (
            OrderStatus.CANCELLED,
            OrderStatus.CANCELLATION_PENDING,
        ):
            return order

        if order.status in (
            OrderStatus.PENDING,
            OrderStatus.PAYMENT_PENDING,
        ):
            raise OrderCannotBeCancelledError(
                order_id=order.id,
                status=order.status,
            )

        if order.status == OrderStatus.COMPLETED:
            order.status = OrderStatus.CANCELLED

        elif order.status == OrderStatus.PAID:
            payment = await payment_repository.get_paid_by_order_id_for_update(order.id)

            if payment is None:
                raise PaidOrderPaymentNotFoundError(order.id)

            order.status = OrderStatus.CANCELLATION_PENDING
            payment.status = PaymentStatus.REFUND_PENDING

            requires_refund = True

        await db.flush()

    if requires_refund:
        await run_in_threadpool(
                refund_order_payment.delay,
                order.id,
            )

    return order
