from dataclasses import dataclass
from typing import Any


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]
    

@dataclass
class LLMResponse:
    content: str | None = None
    tool_call: ToolCall | None = None
    state: object | None = None
    conversation_ref: str | None = None