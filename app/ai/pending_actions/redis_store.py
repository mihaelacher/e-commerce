import json

from redis import Redis

from app.ai.models import PendingAction
from app.ai.pending_actions.store import PendingActionStore


class RedisPendingActionStore(PendingActionStore):
    def __init__(
        self,
        redis: Redis,
        ttl_seconds: int = 600,
    ):
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    def save(
        self,
        action: PendingAction,
    ) -> None:
        key = self._key(action.action_id)

        self.redis.setex(
            key,
            self.ttl_seconds,
            json.dumps(
                {
                    "action_id": action.action_id,
                    "name": action.name,
                    "arguments": action.arguments,
                }
            ),
        )

    def get(
        self,
        action_id: str,
    ) -> PendingAction | None:
        data = self.redis.get(self._key(action_id))

        if data is None:
            return None

        payload = json.loads(data)

        return PendingAction(
            action_id=payload["action_id"],
            name=payload["name"],
            arguments=payload["arguments"],
        )

    def delete(
        self,
        action_id: str,
    ) -> None:
        self.redis.delete(self._key(action_id))

    def _key(
        self,
        action_id: str,
    ) -> str:
        return f"mcp:pending_action:{action_id}"
