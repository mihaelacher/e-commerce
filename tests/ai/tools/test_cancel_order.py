from unittest.mock import MagicMock, patch

import pytest

from app.ai.tools.cancel_order import CancelOrderTool
from app.enums.order import OrderStatus
from app.exceptions.order import OrderCannotBeCancelledError


class FakeOrderRepository:
    def __init__(self, order=None, should_raise=False, raise_exception=None):
        self.order = order
        self.should_raise = should_raise
        self.raise_exception = raise_exception

    def get_with_items_for_update(self, order_id):
        if self.should_raise:
            raise self.raise_exception
        return self.order


def test_cancel_completed_order():
    mocked_order = MagicMock()
    mocked_order.id = 1
    mocked_order.status = OrderStatus.COMPLETED

    mocked_db = MagicMock()

    with patch(
        "app.ai.tools.cancel_order.cancel_order",
        return_value=mocked_order,
    ):
        tool = CancelOrderTool(db=mocked_db)

        result = tool.execute(order_id=1)

        assert result["success"] is True
        assert result["order_id"] == 1
        assert result["status"] == OrderStatus.COMPLETED


def test_cancel_paid_order_with_refund():
    mocked_order = MagicMock()
    mocked_order.id = 1
    mocked_order.status = OrderStatus.CANCELLATION_PENDING
    mocked_order.payment_id = 42

    mocked_db = MagicMock()

    with patch(
        "app.ai.tools.cancel_order.cancel_order",
        return_value=mocked_order,
    ):
        tool = CancelOrderTool(db=mocked_db)

        result = tool.execute(order_id=1)

        assert result["success"] is True
        assert result["order_id"] == 1
        assert result["status"] == OrderStatus.CANCELLATION_PENDING


def test_cancel_pending_order_fails():
    mocked_db = MagicMock()

    with patch(
        "app.ai.tools.cancel_order.cancel_order",
        side_effect=OrderCannotBeCancelledError(
            order_id=1,
            status=OrderStatus.PENDING,
        ),
    ):
        tool = CancelOrderTool(db=mocked_db)

        with pytest.raises(OrderCannotBeCancelledError):
            tool.execute(order_id=1)


def test_cancel_payment_pending_order_fails():
    mocked_db = MagicMock()

    with patch(
        "app.ai.tools.cancel_order.cancel_order",
        side_effect=OrderCannotBeCancelledError(
            order_id=2,
            status=OrderStatus.PAYMENT_PENDING,
        ),
    ):
        tool = CancelOrderTool(db=mocked_db)

        with pytest.raises(OrderCannotBeCancelledError):
            tool.execute(order_id=2)


def test_cancel_already_cancelled_order_is_idempotent():
    mocked_order = MagicMock()
    mocked_order.id = 3
    mocked_order.status = OrderStatus.CANCELLED

    mocked_db = MagicMock()

    with patch(
        "app.ai.tools.cancel_order.cancel_order",
        return_value=mocked_order,
    ):
        tool = CancelOrderTool(db=mocked_db)

        result = tool.execute(order_id=3)

        assert result["success"] is True
        assert result["order_id"] == 3
        assert result["status"] == OrderStatus.CANCELLED


def test_cancel_cancellation_pending_order_is_idempotent():
    mocked_order = MagicMock()
    mocked_order.id = 4
    mocked_order.status = OrderStatus.CANCELLATION_PENDING

    mocked_db = MagicMock()

    with patch(
        "app.ai.tools.cancel_order.cancel_order",
        return_value=mocked_order,
    ):
        tool = CancelOrderTool(db=mocked_db)

        result = tool.execute(order_id=4)

        assert result["success"] is True
        assert result["order_id"] == 4
        assert result["status"] == OrderStatus.CANCELLATION_PENDING


def test_cancel_order_not_found():
    from app.exceptions.checkout import OrderNotFoundError

    mocked_db = MagicMock()

    with patch(
        "app.ai.tools.cancel_order.cancel_order",
        side_effect=OrderNotFoundError(99),
    ):
        tool = CancelOrderTool(db=mocked_db)

        with pytest.raises(OrderNotFoundError):
            tool.execute(order_id=99)


def test_cancel_order_tool_has_correct_definition():
    mocked_db = MagicMock()
    tool = CancelOrderTool(db=mocked_db)

    assert tool.name == "cancel_order"
    assert tool.requires_confirmation is True
    assert tool.definition["name"] == "cancel_order"
    assert "order_id" in tool.definition["parameters"]["properties"]
    assert tool.definition["parameters"]["required"] == ["order_id"]
