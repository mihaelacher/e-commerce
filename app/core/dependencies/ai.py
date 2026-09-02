from typing import Annotated

from fastapi import Depends
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.clients.embedding_base import EmbeddingClient
from app.ai.clients.gemini.client import GeminiClient
from app.ai.clients.gemini.embedding import GeminiEmbeddingClient
from app.ai.clients.llm_base import LLMClient
from app.ai.conversation.redis_store import RedisConversationStore
from app.ai.conversation.store import ConversationStore
from app.ai.tools.cancel_order import CancelOrderTool
from app.ai.tools.get_order_status import GetOrderStatusTool
from app.ai.tools.search_products import SearchProductsTool
from app.core.database import get_async_db
from app.core.dependencies.core import get_redis
from app.repositories.order.async_order import AsyncOrderRepository
from app.repositories.product.async_product import (
    AsyncProductRepository as ProductRepository,
)
from app.services.ai import AIService


def get_ai_client() -> LLMClient:
    return GeminiClient()


def get_embedding_client() -> EmbeddingClient:
    return GeminiEmbeddingClient()


def get_search_products_tool(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    embedding_client: Annotated[EmbeddingClient, Depends(get_embedding_client)],
) -> SearchProductsTool:
    return SearchProductsTool(
        embedding_client=embedding_client,
        product_repository=ProductRepository(db),
    )


def get_order_status_tool(
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> GetOrderStatusTool:
    return GetOrderStatusTool(
        order_repository=AsyncOrderRepository(db),
    )


def get_cancel_order_tool(
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> CancelOrderTool:
    return CancelOrderTool(
        db=db,
    )


def get_conversation_store(
    redis: Annotated[Redis, Depends(get_redis)],
) -> ConversationStore:
    return RedisConversationStore(
        redis=redis,
        ttl_seconds=3600,
    )


def get_ai_service(
    ai_client: Annotated[LLMClient, Depends(get_ai_client)],
    conversation_store: Annotated[
        ConversationStore,
        Depends(get_conversation_store),
    ],
    search_products_tool: Annotated[
        SearchProductsTool,
        Depends(get_search_products_tool),
    ],
    order_status_tool: Annotated[
        GetOrderStatusTool,
        Depends(get_order_status_tool),
    ],
    cancel_order_tool: Annotated[
        CancelOrderTool,
        Depends(get_cancel_order_tool),
    ],
) -> AIService:
    return AIService(
        ai_client=ai_client,
        conversation_store=conversation_store,
        tools=[
            search_products_tool,
            order_status_tool,
            cancel_order_tool,
        ],
    )
