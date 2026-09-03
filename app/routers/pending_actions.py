from typing import Annotated

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.pending_actions.redis_store import RedisPendingActionStore
from app.core.database import get_async_db
from app.core.dependencies.core import get_redis
from app.services.pending_action import approve_pending_action

router = APIRouter(
    prefix="/pending-actions",
    tags=["Pending Actions"],
)


@router.post("/{action_id}/approve")
async def approve_action(
    action_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> dict:
    store = RedisPendingActionStore(
        redis=redis,
    )

    return await approve_pending_action(
        db=db,
        store=store,
        action_id=action_id,
    )
