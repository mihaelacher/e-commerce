from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.pending_actions.store import PendingActionStore
from app.ai.tools.cancel_order import CancelOrderTool
from app.exceptions.pending_action import (
    PendingActionNotFoundError,
    UnsupportedPendingActionError,
)


async def approve_pending_action(
    db: AsyncSession,
    store: PendingActionStore,
    action_id: str,
) -> dict:
    action = await store.get(action_id)

    if action is None:
        raise PendingActionNotFoundError(action_id)

    if action.name != "cancel_order":
        raise UnsupportedPendingActionError(action.name)

    tool = CancelOrderTool(db=db)

    result = await tool.execute(
        **action.arguments,
    )

    await store.delete(action_id)

    return result
