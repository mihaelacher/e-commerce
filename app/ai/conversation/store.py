from abc import ABC, abstractmethod
from typing import Any

from app.ai.models import PendingToolCall


class ConversationStore(ABC):
    @abstractmethod
    async def get(self, conversation_id: str) -> Any | None: ...

    @abstractmethod
    async def save(
        self,
        conversation_id: str,
        state: Any,
    ) -> None: ...

    @abstractmethod
    async def get_pending_tool_call(
        self,
        conversation_id: str,
    ) -> PendingToolCall | None: ...

    @abstractmethod
    async def save_pending_tool_call(
        self,
        conversation_id: str,
        tool_call: PendingToolCall,
    ) -> None: ...

    @abstractmethod
    async def clear_pending_tool_call(
        self,
        conversation_id: str,
    ) -> None: ...
