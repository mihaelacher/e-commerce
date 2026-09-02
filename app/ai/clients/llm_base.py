from abc import ABC, abstractmethod
from typing import Any

from app.ai.models import LLMResponse


class LLMClient(ABC):
    @abstractmethod
    async def chat(
        self,
        message: str,
        tools: list[dict] | None = None,
        state: Any | None = None,
    ) -> LLMResponse: ...

    @abstractmethod
    async def chat_with_tool_result(
        self,
        previous_response: LLMResponse,
        tool_result: Any,
        tools: list[dict] | None = None,
    ) -> LLMResponse: ...

    @abstractmethod
    def serialize_state(
        self,
        state: Any,
    ) -> Any: ...

    @abstractmethod
    def deserialize_state(
        self,
        state: Any,
    ) -> Any: ...
