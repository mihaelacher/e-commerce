import time

from pydantic import ValidationError

from app.ai.clients.llm_base import LLMClient
from app.ai.conversation.store import ConversationStore
from app.ai.models import LLMResponse, PendingToolCall, ToolCall
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIService:
    MAX_AGENT_STEPS = 5

    def __init__(
        self,
        ai_client: LLMClient,
        conversation_store: ConversationStore,
        tools: list,
    ):
        self.ai_client = ai_client
        self.conversation_store = conversation_store
        self.tools = {tool.name: tool for tool in tools}

    async def chat(
        self,
        message: str,
        conversation_id: str,
        confirm_action: bool | None = None,
    ) -> str:
        start_time = time.perf_counter()
        tool_calls: list[str] = []

        try:
            tool_definitions = [tool.definition for tool in self.tools.values()]

            stored_state = self.conversation_store.get(conversation_id)

            state = None

            if stored_state is not None:
                state = self.ai_client.deserialize_state(stored_state)

            pending_tool_call = self.conversation_store.get_pending_tool_call(
                conversation_id
            )

            if pending_tool_call and confirm_action is not None:
                previous_response = LLMResponse(
                    tool_call=ToolCall(
                        name=pending_tool_call.name,
                        arguments=pending_tool_call.arguments,
                    ),
                    state=state,
                )

                if confirm_action is False:
                    tool_result = {
                        "success": False,
                        "cancelled": True,
                        "reason": "User rejected the action.",
                    }

                    self.conversation_store.clear_pending_tool_call(conversation_id)

                    response = await self.ai_client.chat_with_tool_result(
                        previous_response=previous_response,
                        tool_result=tool_result,
                        tools=tool_definitions,
                    )

                else:
                    tool = self.tools.get(pending_tool_call.name)

                    if not tool:
                        raise ValueError(f"Unknown tool: {pending_tool_call.name}")

                    arguments = tool.input_model.model_validate(
                        pending_tool_call.arguments
                    )

                    tool_calls.append(tool.name)

                    tool_result = await tool.execute(**arguments.model_dump())

                    self.conversation_store.clear_pending_tool_call(conversation_id)

                    response = await self.ai_client.chat_with_tool_result(
                        previous_response=previous_response,
                        tool_result=tool_result,
                        tools=tool_definitions,
                    )

            else:
                response = await self.ai_client.chat(
                    message=message,
                    tools=tool_definitions,
                    state=state,
                )

            for _ in range(self.MAX_AGENT_STEPS):
                if not response.tool_call:
                    self._save_state(
                        conversation_id=conversation_id,
                        state=response.state,
                    )

                    logger.info(
                        "ai_request_completed",
                        extra={
                            "conversation_id": conversation_id,
                            "duration_ms": round(
                                (time.perf_counter() - start_time) * 1000,
                                2,
                            ),
                            "tool_calls": tool_calls,
                        },
                    )

                    return response.content or ""

                tool_calls.append(response.tool_call.name)

                tool = self.tools.get(response.tool_call.name)

                if not tool:
                    raise ValueError(f"Unknown tool: {response.tool_call.name}")

                try:
                    arguments = tool.input_model.model_validate(
                        response.tool_call.arguments
                    )
                except ValidationError as exc:
                    tool_result = {
                        "success": False,
                        "error": {
                            "type": "validation_error",
                            "details": exc.errors(
                                include_url=False,
                                include_input=False,
                            ),
                        },
                    }

                    response = await self.ai_client.chat_with_tool_result(
                        previous_response=response,
                        tool_result=tool_result,
                        tools=tool_definitions,
                    )

                    continue

                if getattr(
                    tool,
                    "requires_confirmation",
                    False,
                ):
                    self.conversation_store.save_pending_tool_call(
                        conversation_id=conversation_id,
                        tool_call=PendingToolCall(
                            name=tool.name,
                            arguments=arguments.model_dump(),
                        ),
                    )

                    self._save_state(
                        conversation_id=conversation_id,
                        state=response.state,
                    )

                    return (
                        "Please confirm that you want to execute "
                        f"{tool.name} with "
                        f"{arguments.model_dump()}."
                    )

                tool_result = await tool.execute(**arguments.model_dump())

                response = await self.ai_client.chat_with_tool_result(
                    previous_response=response,
                    tool_result=tool_result,
                    tools=tool_definitions,
                )

            raise RuntimeError("Maximum number of agent steps exceeded.")

        except Exception:
            logger.exception(
                "ai_request_failed",
                extra={
                    "conversation_id": conversation_id,
                    "duration_ms": round(
                        (time.perf_counter() - start_time) * 1000,
                        2,
                    ),
                    "tool_calls": tool_calls,
                },
            )
            raise

    def _save_state(
        self,
        conversation_id: str,
        state,
    ) -> None:
        serialized_state = self.ai_client.serialize_state(state)

        self.conversation_store.save(
            conversation_id,
            serialized_state,
        )
