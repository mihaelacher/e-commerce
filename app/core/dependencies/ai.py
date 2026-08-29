from fastapi import Depends
from sqlalchemy.orm import Session

from app.ai.clients.embedding_base import EmbeddingClient
from app.ai.clients.gemini.client import GeminiClient
from app.ai.clients.gemini.embedding import GeminiEmbeddingClient
from app.ai.clients.llm_base import LLMClient
from app.ai.tools.get_order_status import GetOrderStatusTool
from app.ai.tools.search_products import SearchProductsTool
from app.core.database import get_db
from app.repositories.order import OrderRepository
from app.repositories.product import ProductRepository
from app.services.ai import AIService


def get_ai_client() -> LLMClient:
    return GeminiClient()


def get_embedding_client() -> EmbeddingClient:
    return GeminiEmbeddingClient()


def get_search_products_tool(
    db: Session = Depends(get_db),
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
) -> SearchProductsTool:
    return SearchProductsTool(
        embedding_client=embedding_client,
        product_repository=ProductRepository(db),
    )


def get_order_status_tool(
    db: Session = Depends(get_db),
) -> GetOrderStatusTool:
    return GetOrderStatusTool(
        order_repository=OrderRepository(db),
    )


def get_ai_service(
    ai_client: LLMClient = Depends(get_ai_client),
    search_products_tool: SearchProductsTool = Depends(
        get_search_products_tool
    ),
    order_status_tool: GetOrderStatusTool = Depends(
        get_order_status_tool
    ),
) -> AIService:
    return AIService(
        ai_client=ai_client,
        tools=[
            search_products_tool,
            order_status_tool,
        ],
    )