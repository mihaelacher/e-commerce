import json

from redis import Redis

from app.ai.conversation.store import ConversationStore


class RedisConversationStore(ConversationStore):
    def __init__(
        self,
        redis: Redis,
        ttl_seconds: int = 3600,
    ):
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    def get(self, conversation_id: str):
        value = self.redis.get(
            self._key(conversation_id)
        )

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

    @staticmethod
    def _key(conversation_id: str) -> str:
        return f"ai:conversation:{conversation_id}"