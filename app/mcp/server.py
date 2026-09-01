from mcp.server import MCPServer

from app.ai.tools.cancel_order import CancelOrderTool
from app.ai.tools.get_order_status import GetOrderStatusTool
from app.ai.tools.search_products import SearchProductsTool
from app.core.database import SessionLocal
from app.core.dependencies.ai import get_embedding_client
from app.repositories.order import OrderRepository
from app.repositories.product import ProductRepository

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


embedding_client = LazyEmbeddingClient()


@mcp.tool()
def ping() -> str:
    """Check if the server is running."""
    return "pong"


@mcp.tool()
def search_products(
    query: str,
    min_price: float | None = None,
    max_price: float | None = None,
) -> list[dict]:
    with SessionLocal() as db:
        tool = SearchProductsTool(
            embedding_client=embedding_client,
            product_repository=ProductRepository(db=db),
        )

        return tool.execute(
            query=query,
            min_price=min_price,
            max_price=max_price,
        )


@mcp.tool()
def get_order_status(order_id: int) -> dict:
    with SessionLocal() as db:
        tool = GetOrderStatusTool(
            order_repository=OrderRepository(db=db),
        )

        return tool.execute(order_id=order_id)


@mcp.tool()
def cancel_order(order_id: int) -> dict:
    with SessionLocal() as db:
        tool = CancelOrderTool(
            db=db,
        )

        return tool.execute(order_id=order_id)        


if __name__ == "__main__":
    mcp.run()