import uuid

from sqlalchemy import select

from app.core.database import SessionLocal, transaction
from app.enums.order import OrderStatus
from app.enums.payment_provider import PaymentProvider
from app.enums.payment_status import PaymentStatus
from app.models.order import OrderModel
from app.repositories.payment import PaymentRepository


def seed_payments() -> None:
    db = SessionLocal()

    try:
        payment_repository = PaymentRepository(db)

        orders = db.scalars(
            select(OrderModel)
        ).all()

        if not orders:
            raise RuntimeError(
                "No orders found. Seed orders first."
            )

        payment_count = 0

        with transaction(db):
            for order in orders:
                if order.status in {
                    OrderStatus.COMPLETED,
                    OrderStatus.PAID,
                }:
                    status = PaymentStatus.PAID

                elif order.status == OrderStatus.PAYMENT_PENDING:
                    status = PaymentStatus.PENDING

                elif order.status == OrderStatus.CANCELLED:
                    status = PaymentStatus.FAILED

                else:
                    continue

                payment = payment_repository.create(
                    order_id=order.id,
                    amount=order.total,
                    provider=PaymentProvider.MOCK,
                    idempotency_key=str(uuid.uuid4()),
                )

                payment.status = status

                if status == PaymentStatus.PAID:
                    payment.transaction_id = (
                        f"mock_tx_{uuid.uuid4().hex}"
                    )

                payment_count += 1

        print(f"Seeded {payment_count} payments.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_payments()