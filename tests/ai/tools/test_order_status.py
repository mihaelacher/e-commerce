from datetime import datetime
from types import SimpleNamespace
from unittest import result

from app.ai.tools.get_order_status import GetOrderStatusTool


class FakeOrderRepository:
    def get(self, order_id: int):
        return SimpleNamespace(
            id=order_id,
            status="processing",
            created_at=datetime(2026, 8, 29, 12, 0),
        )


class EmptyOrderRepository:
    def get(self, order_id: int):
        return None    


def test_get_order_status():
    tool = GetOrderStatusTool(
        order_repository=FakeOrderRepository(),
    )

    result = tool.execute(order_id=42)

    assert result["order_id"] == 42
    assert result["status"] == "processing"


def test_get_order_status_when_order_does_not_exist():
    tool = GetOrderStatusTool(
        order_repository=EmptyOrderRepository(),
    )

    result = tool.execute(order_id=999)

    assert result == {
        "order_id": 999,
        "found": False,
    }
