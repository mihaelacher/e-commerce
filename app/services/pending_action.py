from sqlalchemy.orm import Session

from app.ai.pending_actions.store import PendingActionStore
from app.ai.tools.cancel_order import CancelOrderTool
from app.exceptions.pending_action import (
    PendingActionNotFoundError,
    UnsupportedPendingActionError,
)


def approve_pending_action(
    db: Session,
    store: PendingActionStore,
    action_id: str,
) -> dict:
    action = store.get(action_id)

    if action is None:
        raise PendingActionNotFoundError(action_id)

    if action.name != "cancel_order":
        raise UnsupportedPendingActionError(action.name)

    tool = CancelOrderTool(db=db)

    result = tool.execute(
        **action.arguments,
    )

    store.delete(action_id)

    return result