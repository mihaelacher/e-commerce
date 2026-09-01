from app.core.database import SessionLocal, transaction
from app.core.dependencies.payment import get_payment_provider
from app.enums.order import OrderStatus
from app.enums.payment_status import PaymentStatus
from app.repositories.order import OrderRepository
from app.repositories.payment import PaymentRepository
from app.repositories.product import ProductRepository
from app.tasks.celery import celery_app


@celery_app.task(
    bind=True,
    autoretry_for=(TimeoutError, ConnectionError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def refund_order_payment(
    self,
    order_id: int,
):
    with SessionLocal() as db:
        payment_repository = PaymentRepository(db)
        order_repository = OrderRepository(db)
        product_repository = ProductRepository(db)

        payment = payment_repository.get_refund_pending_by_order_id(
            order_id
        )

        if payment is None:
            return

        payment_provider = get_payment_provider()

        result = payment_provider.refund(
            transaction_id=payment.transaction_id,
            amount=payment.amount,
            idempotency_key=f"refund-payment-{payment.id}",
        )

        if not result.success:
            with transaction(db):
                order = order_repository.get_for_update(
                    order_id
                )

                payment = payment_repository.get_for_update(
                    payment.id
                )

                if order is None or payment is None:
                    raise RuntimeError(
                        "Order/payment disappeared during refund processing."
                    )

                payment.status = PaymentStatus.PAID
                order.status = OrderStatus.PAID

                db.flush()

            return

        with transaction(db):
            order = order_repository.get_with_items_for_update(
                order_id
            )

            payment = payment_repository.get_for_update(
                payment.id
            )

            if order is None or payment is None:
                raise RuntimeError(
                    "Order/payment disappeared during refund processing."
                )

            if payment.status == PaymentStatus.REFUNDED:
                return

            for item in order.items:
                product = product_repository.get_with_lock(
                    item.product_id
                )

                product.stock += item.quantity

            payment.status = PaymentStatus.REFUNDED
            order.status = OrderStatus.CANCELLED

            db.flush()