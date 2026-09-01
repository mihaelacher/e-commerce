from abc import ABC, abstractmethod
from typing import Any

from app.ai.models import PendingToolCall


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

    @abstractmethod
    def get_pending_tool_call(
        self,
        conversation_id: str,
    ) -> PendingToolCall | None:
        ...

    @abstractmethod
    def save_pending_tool_call(
        self,
        conversation_id: str,
        tool_call: PendingToolCall,
    ) -> None:
        ...

    @abstractmethod
    def clear_pending_tool_call(
        self,
        conversation_id: str,
    ) -> None:
        ...