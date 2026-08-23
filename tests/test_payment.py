from decimal import Decimal

import pytest
import pytest
from sqlalchemy.orm import Session

from app.enums.order import OrderStatus
from app.enums.payment_provider import PaymentProvider
from app.enums.payment_status import PaymentStatus
from app.exceptions.payment import OrderCannotBePaidError
from app.exceptions.payment import OrderCannotBePaidError
from app.models.order import OrderModel
from app.models.order_item import OrderItemModel
from app.models.payment import PaymentModel
from app.models.product import ProductModel
from app.providers.payment.base import PaymentResult
from app.providers.payment.mock import MockPaymentProvider
from app.services.checkout import checkout
from app.services.payment import create_payment, handle_payment_webhook
from app.tasks.payment import process_payment
from tests.conftest import db

def test_create_payment_success(db):
    order = create_order(db)

    payment = create_payment(
        db=db,
        order_id=order.id,
        idempotency_key="test-key-1",
        provider=MockPaymentProvider(),
    )

    assert payment.status == PaymentStatus.PENDING
    assert payment.transaction_id is None
    assert payment.order_id == order.id
    assert payment.amount == order.total

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

def test_process_payment(
    db,
    monkeypatch,
    testing_session_factory
):
    order = create_order(db)
    
    payment = PaymentModel(
        order_id=order.id,
        amount=Decimal("100.00"),
        status=PaymentStatus.PENDING,
        provider=PaymentProvider.MOCK,
        idempotency_key="test-key",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    class MockProvider:
        def charge(self, amount, idempotency_key):
            return PaymentResult(
                success=True,
                transaction_id="mock_transaction_123",
            )

    monkeypatch.setattr(
        "app.tasks.payment.get_payment_provider",
        lambda: MockProvider(),
    )

    monkeypatch.setattr(
        "app.tasks.payment.SessionLocal",
        testing_session_factory,
    )

    process_payment(payment.id)

    db.expire_all()

    payment = db.get(PaymentModel, payment.id)

    assert payment.transaction_id == "mock_transaction_123"
    assert payment.status == PaymentStatus.PENDING


def test_process_payment_payment_not_found():
    process_payment(999999)   


def test_process_payment_skips_non_pending_payment(
    db,
    monkeypatch,
):
    order = create_order(db)

    payment = PaymentModel(
        order_id=order.id,
        amount=Decimal("100.00"),
        status=PaymentStatus.PAID,
        provider=PaymentProvider.MOCK,
        idempotency_key="test-key",
        transaction_id="mock_transaction_123",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("Provider should not be called")

    monkeypatch.setattr(
        MockPaymentProvider,
        "charge",
        fail_if_called,
    )

    process_payment(payment.id)    


def test_process_payment_failure(
    db,
    monkeypatch,
    testing_session_factory
):
    order = create_order(db)

    payment = PaymentModel(
        order_id=order.id,
        amount=Decimal("100.00"),
        status=PaymentStatus.PENDING,
        provider=PaymentProvider.MOCK,
        idempotency_key="test-key",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    class MockProvider:
        def charge(self, amount, idempotency_key):
            return PaymentResult(
                success=False,
                transaction_id="mock_transaction_456",
            )

    monkeypatch.setattr(
        "app.tasks.payment.get_payment_provider",
        lambda: MockProvider(),
    )

    monkeypatch.setattr(
          "app.tasks.payment.SessionLocal",
          testing_session_factory,
      )

    process_payment(payment.id)

    db.expire_all()

    payment = db.get(PaymentModel, payment.id)

    assert payment.transaction_id == "mock_transaction_456"
    assert payment.status == PaymentStatus.PENDING


def test_process_payment_retries_and_releases_claim(
    db,
    monkeypatch,
    testing_session_factory,
):
    order = create_order(db)

    payment = PaymentModel(
        order_id=order.id,
        amount=Decimal("100.00"),
        status=PaymentStatus.PENDING,
        provider=PaymentProvider.MOCK,
        idempotency_key="test-key-retry",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    class FailingProvider:
        def charge(self, amount, idempotency_key):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(
        "app.tasks.payment.get_payment_provider",
        lambda: FailingProvider(),
    )
    monkeypatch.setattr(
        "app.tasks.payment.SessionLocal",
        testing_session_factory,
    )

    with pytest.raises(RuntimeError, match="provider unavailable"):
        process_payment(payment.id)

    db.expire_all()
    payment = db.get(PaymentModel, payment.id)

    assert payment.status == PaymentStatus.PENDING
    assert payment.processing_started_at is None
    assert process_payment.autoretry_for == (Exception,)
    assert process_payment.max_retries == 3

def test_payment_webhook_success(db, monkeypatch):
    order = create_order(db)

    payment = PaymentModel(
        order_id=order.id,
        amount=Decimal("100.00"),
        status=PaymentStatus.PENDING,
        provider=PaymentProvider.MOCK,
        idempotency_key="test-key",
        transaction_id="mock_transaction_123",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    provider = MockPaymentProvider()
    confirmation_calls = []

    monkeypatch.setattr(
        "app.services.payment.send_order_confirmation_task.delay",
        lambda **kwargs: confirmation_calls.append(kwargs),
    )

    payment = handle_payment_webhook(
        db=db,
        payload={
            "status": "success",
            "transaction_id": "mock_transaction_123",
        },
        provider=provider,
    )

    db.refresh(order)

    assert payment.status == PaymentStatus.PAID
    assert order.status == OrderStatus.PAID   
    assert confirmation_calls == [
        {
            "recipient": "test@example.com",
            "order_id": order.id,
            "total": "100.00",
        }
    ]


def test_payment_webhook_failure(db, monkeypatch):
    order = create_order(db)

    payment = PaymentModel(
        order_id=order.id,
        amount=Decimal("100.00"),
        status=PaymentStatus.PENDING,
        provider=PaymentProvider.MOCK,
        idempotency_key="test-key",
        transaction_id="mock_transaction_456",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    provider = MockPaymentProvider()

    monkeypatch.setattr(
        "app.services.payment.send_order_confirmation_task.delay",
        lambda **kwargs: pytest.fail("Confirmation must not be sent for failed payment"),
    )

    payment = handle_payment_webhook(
        db=db,
        payload={
            "status": "failed",
            "transaction_id": "mock_transaction_456",
        },
        provider=provider,
    )

    db.refresh(order)

    assert payment.status == PaymentStatus.FAILED
    assert order.status == OrderStatus.PENDING


def test_failed_payment_releases_stock_and_allows_checkout_again(db):
    order = create_order(db)
    product = ProductModel(name="Keyboard", price=Decimal("50.00"), stock=3)
    db.add(product)
    db.flush()

    order_item = OrderItemModel(
        order_id=order.id,
        product_id=product.id,
        quantity=2,
        unit_price=product.price,
        total_price=Decimal("100.00"),
    )
    db.add(order_item)
    product.stock -= order_item.quantity

    payment = PaymentModel(
        order_id=order.id,
        amount=Decimal("100.00"),
        status=PaymentStatus.PENDING,
        provider=PaymentProvider.MOCK,
        idempotency_key="test-key-stock-release",
        transaction_id="mock_transaction_stock_release",
    )
    db.add(payment)
    db.commit()

    handle_payment_webhook(
        db=db,
        payload={
            "status": "failed",
            "transaction_id": "mock_transaction_stock_release",
        },
        provider=MockPaymentProvider(),
    )

    db.refresh(product)
    db.refresh(order)

    assert product.stock == 3
    assert order.status == OrderStatus.PENDING

    checkout(db, order.id)

    db.refresh(product)
    db.refresh(order)

    assert product.stock == 1
    assert order.status == OrderStatus.PAYMENT_PENDING

def test_payment_webhook_ignores_processed_payment(db):
    order = create_order(db)

    payment = PaymentModel(
        order_id=order.id,
        amount=Decimal("100.00"),
        status=PaymentStatus.PAID,
        provider=PaymentProvider.MOCK,
        idempotency_key="test-key",
        transaction_id="mock_transaction_789",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    payment = handle_payment_webhook(
        db=db,
        payload={
            "status": "failed",
            "transaction_id": "mock_transaction_789",
        },
        provider=MockPaymentProvider(),
    )

    db.refresh(order)

    assert order.status == OrderStatus.PAYMENT_PENDING    


def test_failed_payment_can_be_retried(db):
    order = create_order(db)

    failed_payment = PaymentModel(
        order_id=order.id,
        amount=Decimal("100.00"),
        status=PaymentStatus.FAILED,
        provider=PaymentProvider.MOCK,
        idempotency_key="first-attempt",
        transaction_id="mock_failed_123",
    )

    db.add(failed_payment)
    db.commit()
    db.refresh(failed_payment)

    retry_payment = create_payment(
        db=db,
        order_id=order.id,
        idempotency_key="second-attempt",
        provider=MockPaymentProvider(),
    )

    assert retry_payment.id != failed_payment.id
    assert retry_payment.order_id == order.id
    assert retry_payment.status == PaymentStatus.PENDING
    assert retry_payment.transaction_id is None    

    db.refresh(order)

    assert order.status == OrderStatus.PAYMENT_PENDING    

    db.refresh(order)

    assert {payment.id for payment in order.payments} == {
        failed_payment.id,
        retry_payment.id,
    }


def test_payment_cannot_be_created_for_already_paid_order(db):
    order = create_order(db)

    successful_payment = PaymentModel(
        order_id=order.id,
        amount=Decimal("100.00"),
        status=PaymentStatus.PAID,
        provider=PaymentProvider.MOCK,
        idempotency_key="first-payment",
        transaction_id="mock_transaction_123",
    )

    db.add(successful_payment)
    db.commit()

    with pytest.raises(OrderCannotBePaidError):
        create_payment(
            db=db,
            order_id=order.id,
            idempotency_key="second-payment",
            provider=MockPaymentProvider(),
        )