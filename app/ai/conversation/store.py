from abc import ABC, abstractmethod
from typing import Any


class ConversationStore(ABC):
    @abstractmethod
    def get(self, conversation_id: str) -> Any | None:
        ...

    @abstractmethod
    def save(
        self,
        conversation_id: str,
        state: Any,
    ) -> None:
        ...