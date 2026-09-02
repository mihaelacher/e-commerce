from time import perf_counter
from typing import Any

from google import genai
from google.genai import types

from app.ai.clients.gemini.helper import with_retry
from app.ai.clients.llm_base import LLMClient
from app.ai.models import LLMResponse, ToolCall
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

SYSTEM_INSTRUCTION = (
        "You are an assistant for an e-commerce application. "
        "Use the provided tools to perform supported actions and retrieve "
        "application data when needed. "
        "If the user explicitly requests an action and an appropriate tool "
        "is available, use that tool instead of claiming that you cannot "
        "perform the action. "
        "Do not invent products, prices, stock, order information, "
        "tool results, or application capabilities. "
        "Answer clearly and concisely."
    )


class GeminiClient(LLMClient):
    def __init__(self) -> None:
        self.model = "gemini-3.6-flash"

        self.client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(
                timeout=settings.ai_client_timeout_ms,
            ),
        )

    def chat(
        self,
        message: str,
        tools: list[dict] | None = None,
        state: Any | None = None,
    ) -> LLMResponse:
        start_time = perf_counter()

        def request():
            user_content = types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=message),
                ],
            )

            contents = [
                *(state or []),
                user_content,
            ]

            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=self._build_tools(tools),
                ),
            )

            new_state = [
                *contents,
                response.candidates[0].content,
            ]

            self._log_completed_call(
                operation="chat",
                start_time=start_time,
                usage_metadata=response.usage_metadata,
            )

            return self._to_response(
                response=response,
                state=new_state,
            )

        try:
            return with_retry(request)
        except Exception:
            self._log_failed_call(
                operation="chat",
                start_time=start_time,
            )
            raise

    def chat_with_tool_result(
        self,
        previous_response: LLMResponse,
        tool_result: Any,
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        start_time = perf_counter()

        def request():
            function_response = types.Content(
                role="user",
                parts=[
                    types.Part.from_function_response(
                        name=previous_response.tool_call.name,
                        response={
                            "result": tool_result,
                        },
                    )
                ],
            )

            contents = [
                *previous_response.state,
                function_response,
            ]

            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=self._build_tools(tools),
                ),
            )

            new_state = [
                *contents,
                response.candidates[0].content,
            ]

            self._log_completed_call(
                operation="tool_result",
                start_time=start_time,
                usage_metadata=response.usage_metadata,
            )

            return self._to_response(
                response=response,
                state=new_state,
            )

        try:
            return with_retry(request)
        except Exception:
            self._log_failed_call(
                operation="tool_result",
                start_time=start_time,
            )
            raise

    def serialize_state(
        self,
        state: Any,
    ) -> list[dict]:
        return [
            content.model_dump(
                mode="json",
                exclude_none=True,
            )
            for content in state
        ]

    def deserialize_state(
        self,
        state: list[dict],
    ) -> list[types.Content]:
        return [
            types.Content.model_validate(content)
            for content in state
        ]

    def _build_tools(
        self,
        tools: list[dict] | None,
    ) -> list[types.Tool] | None:
        if not tools:
            return None

        return [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name=tool["name"],
                        description=tool["description"],
                        parameters=tool["parameters"],
                    )
                    for tool in tools
                ]
            )
        ]

    def _to_response(
        self,
        response,
        state: list[types.Content],
    ) -> LLMResponse:
        if response.function_calls:
            function_call = response.function_calls[0]

            return LLMResponse(
                tool_call=ToolCall(
                    name=function_call.name,
                    arguments=dict(function_call.args),
                ),
                state=state,
            )

        return LLMResponse(
            content=response.text,
            state=state,
        )

    def _log_completed_call(
        self,
        operation: str,
        start_time: float,
        usage_metadata,
    ) -> None:
        logger.info(
            "llm_call_completed",
            extra={
                "provider": "gemini",
                "model": self.model,
                "operation": operation,
                "duration_ms": round(
                    (perf_counter() - start_time) * 1000,
                    2,
                ),
                "prompt_tokens": (
                    usage_metadata.prompt_token_count
                    if usage_metadata
                    else None
                ),
                "completion_tokens": (
                    usage_metadata.candidates_token_count
                    if usage_metadata
                    else None
                ),
                "thought_tokens": (
                    usage_metadata.thoughts_token_count
                    if usage_metadata
                    else None
                ),
                "total_tokens": (
                    usage_metadata.total_token_count
                    if usage_metadata
                    else None
                ),
            },
        )

    def _log_failed_call(
        self,
        operation: str,
        start_time: float,
    ) -> None:
        logger.exception(
            "llm_call_failed",
            extra={
                "provider": "gemini",
                "model": self.model,
                "operation": operation,
                "duration_ms": round(
                    (perf_counter() - start_time) * 1000,
                    2,
                ),
            },
        )