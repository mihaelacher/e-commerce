from uuid import uuid4

from mcp.server import MCPServer

from app.ai.models import PendingAction
from app.ai.pending_actions.redis_store import RedisPendingActionStore
from app.ai.tools.get_order_status import GetOrderStatusTool
from app.ai.tools.search_products import SearchProductsTool
from app.core.database import AsyncSessionLocal
from app.core.dependencies.ai import get_embedding_client
from app.core.dependencies.core import get_redis
from app.repositories.order.async_order import AsyncOrderRepository as OrderRepository
from app.repositories.product.async_product import (
    AsyncProductRepository as ProductRepository,
)

mcp = MCPServer("ecommerce")


class LazyEmbeddingClient:
    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = get_embedding_client()
        return self._client

    def embed(self, text: str) -> list[float]:
        return self._get_client().embed(text)

    async def embed_async(self, text: str) -> list[float]:
        return await self._get_client().embed_async(text)


embedding_client = LazyEmbeddingClient()


@mcp.tool()
def ping() -> str:
    """Check if the server is running."""
    return "pong"


@mcp.tool()
async def search_products(
    query: str,
    min_price: float | None = None,
    max_price: float | None = None,
) -> list[dict]:
    async with AsyncSessionLocal() as db:
        tool = SearchProductsTool(
            embedding_client=embedding_client,
            product_repository=ProductRepository(db=db),
        )

        return await tool.execute(
            query=query,
            min_price=min_price,
            max_price=max_price,
        )


@mcp.tool()
async def get_order_status(order_id: int) -> dict:
    async with AsyncSessionLocal() as db:
        tool = GetOrderStatusTool(
            order_repository=OrderRepository(db=db),
        )

        return await tool.execute(order_id=order_id)


@mcp.tool()
def request_order_cancellation(
    order_id: int,
) -> dict:
    action_id = str(uuid4())

    store = RedisPendingActionStore(
        redis=get_redis(),
    )

    store.save(
        PendingAction(
            action_id=action_id,
            name="cancel_order",
            arguments={
                "order_id": order_id,
            },
        )
    )

    return {
        "status": "confirmation_required",
        "action_id": action_id,
        "action": "cancel_order",
        "arguments": {
            "order_id": order_id,
        },
    }


if __name__ == "__main__":
    mcp.run()
