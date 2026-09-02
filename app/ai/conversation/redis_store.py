import json

from redis import Redis

from app.ai.conversation.store import ConversationStore
from app.ai.models import PendingToolCall


class RedisConversationStore(ConversationStore):
    def __init__(
        self,
        redis: Redis,
        ttl_seconds: int = 3600,
    ):
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    def get(self, conversation_id: str):
        value = self.redis.get(self._key(conversation_id))

        if value is None:
            return None

        return json.loads(value)

    def save(
        self,
        conversation_id: str,
        state,
    ) -> None:
        self.redis.set(
            self._key(conversation_id),
            json.dumps(state),
            ex=self.ttl_seconds,
        )

    def get_pending_tool_call(
        self,
        conversation_id: str,
    ) -> PendingToolCall | None:
        value = self.redis.get(self._pending_tool_key(conversation_id))

        if value is None:
            return None

        data = json.loads(value)

        return PendingToolCall(
            name=data["name"],
            arguments=data["arguments"],
        )

    def save_pending_tool_call(
        self,
        conversation_id: str,
        tool_call: PendingToolCall,
    ) -> None:
        self.redis.set(
            self._pending_tool_key(conversation_id),
            json.dumps(
                {
                    "name": tool_call.name,
                    "arguments": tool_call.arguments,
                }
            ),
            ex=self.ttl_seconds,
        )

    def clear_pending_tool_call(
        self,
        conversation_id: str,
    ) -> None:
        self.redis.delete(self._pending_tool_key(conversation_id))

    @staticmethod
    def _key(conversation_id: str) -> str:
        return f"ai:conversation:{conversation_id}"

    @staticmethod
    def _pending_tool_key(
        conversation_id: str,
    ) -> str:
        return f"ai:conversation:{conversation_id}:pending_tool"
