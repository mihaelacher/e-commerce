import json
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from mcp import Client

from app.mcp.server import mcp


def create_order(client: TestClient, *, email: str = "customer@example.com") -> dict:
    response = client.post(
        "/checkout/orders",
        json={"email": email},
    )

    assert response.status_code == 201

    return response.json()



@pytest.mark.anyio
async def test_available_tools() -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()

        tool_names = {tool.name for tool in tools.tools}

        assert "ping" in tool_names
        assert "search_products" in tool_names
        assert "get_order_status" in tool_names
        assert "cancel_order" in tool_names


@pytest.mark.anyio
async def test_ping() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool("ping", {})

        assert result.is_error is False
        assert result.structured_content == {
            "result": "pong",
        }


@pytest.mark.anyio
async def test_search_products() -> None:
    mocked_product = MagicMock()
    mocked_product.name = "Laptop Stand"
    mocked_product.price = Decimal("49.99")
    mocked_product.stock = 5
    mocked_product.description = "Adjustable stand"
    
    mocked_products = [
        (mocked_product, 0.2),
    ]

    with (
        patch(
            "app.mcp.server.embedding_client.embed",
            return_value=[0.1, 0.2, 0.3],
        ),
        patch(
            "app.mcp.server.ProductRepository.semantic_search",
            return_value=mocked_products,
        ),
    ):
        async with Client(mcp) as client:
            result = await client.call_tool(
                "search_products",
                {"query": "laptop"},
            )

    assert result.is_error is False
    assert result.structured_content is not None

    products = [
        json.loads(item.text)
        for item in result.content
    ]

    assert len(products) == 1

    product = products[0]

    assert product["name"] == "Laptop Stand"
    assert product["price"] == "49.99"
    assert product["stock"] == 5
    assert product["description"] == "Adjustable stand"


@pytest.mark.anyio
async def test_get_order_status() -> None:
    mocked_order = MagicMock(
        id=1,
        status="payment_pending",
    )
    mocked_order.created_at = datetime(2026, 8, 31, 10, 0, tzinfo=UTC)

    with patch(
        "app.mcp.server.OrderRepository.get",
        return_value=mocked_order,
    ) as get_order:
        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_order_status",
                {"order_id": 1},
            )

    assert result.is_error is False

    order = json.loads(result.content[0].text)

    assert order["order_id"] == 1
    assert order["status"] == "payment_pending"

    get_order.assert_called_once_with(1)


@pytest.mark.anyio
async def test_cancel_order() -> None:
    mocked_order = MagicMock(
        id=5,
        status="completed",
    )

    with patch(
        "app.ai.tools.cancel_order.cancel_order",
        return_value=mocked_order,
    ):
        async with Client(mcp) as client:
            result = await client.call_tool(
                "cancel_order",
                {"order_id": 5},
            )

    assert result.is_error is False

    response = json.loads(result.content[0].text)

    assert response["success"] is True
    assert response["order_id"] == 5
    assert response["status"] == "completed"


@pytest.mark.anyio
async def test_cancel_order_fails_when_order_not_found() -> None:
    from app.exceptions.checkout import OrderNotFoundError

    with patch(
        "app.services.order.cancel_order",
        side_effect=OrderNotFoundError(999),
    ):
        async with Client(mcp) as client:
            result = await client.call_tool(
                "cancel_order",
                {"order_id": 999},
            )

    assert result.is_error is True


@pytest.mark.anyio
async def test_cancel_order_fails_for_pending_order() -> None:
    from app.enums.order import OrderStatus
    from app.exceptions.order import OrderCannotBeCancelledError

    with patch(
        "app.services.order.cancel_order",
        side_effect=OrderCannotBeCancelledError(
            order_id=6,
            status=OrderStatus.PENDING,
        ),
    ):
        async with Client(mcp) as client:
            result = await client.call_tool(
                "cancel_order",
                {"order_id": 6},
            )

    assert result.is_error is True