import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.ai.tools.get_order_status import GetOrderStatusTool


class FakeOrderRepository:
    async def get(self, order_id: int):
        return await asyncio.sleep(0.1) or SimpleNamespace(
            id=order_id,
            status="processing",
            created_at=datetime(2026, 8, 29, 12, 0, tzinfo=UTC),
        )


class EmptyOrderRepository:
    async def get(self, order_id: int):
        return None


@pytest.mark.anyio
async def test_get_order_status():
    tool = GetOrderStatusTool(
        order_repository=FakeOrderRepository(),
    )

    execution_result = await tool.execute(order_id=42)

    assert execution_result["order_id"] == 42
    assert execution_result["status"] == "processing"


@pytest.mark.anyio
async def test_get_order_status_when_order_does_not_exist():
    tool = GetOrderStatusTool(
        order_repository=EmptyOrderRepository(),
    )

    execution_result = await tool.execute(order_id=999)

    assert execution_result == {
        "order_id": 999,
        "found": False,
    }
