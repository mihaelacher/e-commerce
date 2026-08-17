from decimal import Decimal

from pytest import Session

from app.enums.order import OrderStatus
from app.enums.payment_status import PaymentStatus
from app.models.order import OrderModel
from app.providers.payment.mock import MockPaymentProvider
from app.services.payment import create_payment


def test_create_payment_success(db):
    order = create_order(db)
    
    provider = MockPaymentProvider(should_succeed=True)

    payment = create_payment(
        db=db,
        order_id=order.id,
        idempotency_key="test-key-1",
        provider=provider,
    )

    assert payment.status == PaymentStatus.PAID
    assert payment.transaction_id is not None
    assert payment.order_id == order.id
    assert payment.amount == order.total

    db.refresh(order)

    assert order.status == OrderStatus.PAID


def test_create_payment_failure(db):
    order = create_order(db)

    provider = MockPaymentProvider(should_succeed=False)

    payment = create_payment(
        db=db,
        order_id=order.id,
        idempotency_key="test-key-2",
        provider=provider,
    )

    assert payment.status == PaymentStatus.FAILED
    assert payment.transaction_id is None

    db.refresh(order)

    assert order.status == OrderStatus.PAYMENT_PENDING


def test_create_payment_is_idempotent(db):
    order = create_order(db)
    
    provider = MockPaymentProvider(should_succeed=True)

    first_payment = create_payment(
        db=db,
        order_id=order.id,
        idempotency_key="same-key",
        provider=provider,
    )

    second_payment = create_payment(
        db=db,
        order_id=order.id,
        idempotency_key="same-key",
        provider=provider,
    )

    assert first_payment.id == second_payment.id


def test_same_idempotency_key_can_be_used_for_different_orders(db):
    order = create_order(db)
    another_pending_order = create_order(db)

    provider = MockPaymentProvider(should_succeed=True)

    first_payment = create_payment(
        db=db,
        order_id=order.id,
        idempotency_key="same-key",
        provider=provider,
    )

    second_payment = create_payment(
        db=db,
        order_id=another_pending_order.id,
        idempotency_key="same-key",
        provider=provider,
    )

    assert first_payment.id != second_payment.id


def create_order(db: Session) -> OrderModel:
    order = OrderModel(email="test@example.com" )
    order.total = Decimal("100.00")
    order.status = OrderStatus.PAYMENT_PENDING

    db.add(order)
    db.commit()
    db.refresh(order)

    return order            