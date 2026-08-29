from abc import ABC, abstractmethod

from app.ai.models import LLMResponse


class LLMClient(ABC):
    @abstractmethod
    def chat(
        self,
        message: str
    ) -> LLMResponse:
        pass

    def chat_with_tool_result(
        self,
        previous_response: LLMResponse,
        tool_result: list[dict],
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        pass