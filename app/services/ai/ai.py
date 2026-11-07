import time

from pydantic import ValidationError

from app.ai.clients.llm_base import LLMClient
from app.ai.conversation.store import ConversationStore
from app.ai.models import LLMResponse, PendingToolCall, ToolCall
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIService:
    MAX_AGENT_STEPS = 5
    MAX_TOOL_CALLS_PER_BATCH = 5
    MAX_TOOL_CALLS_PER_REQUEST = 10

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
        tool_call_count = 0

        try:
            tool_definitions = [tool.definition for tool in self.tools.values()]

            stored_state = await self.conversation_store.get(conversation_id)

            state = None

            if stored_state is not None:
                state = self.ai_client.deserialize_state(stored_state)

            pending_tool_call = await self.conversation_store.get_pending_tool_call(
                conversation_id
            )

            if pending_tool_call and confirm_action is not None:
                previous_response = LLMResponse(
                    tool_calls=[
                        ToolCall(
                            name=pending_tool_call.name,
                            arguments=pending_tool_call.arguments,
                        )
                    ],
                    state=state,
                )

                if confirm_action is False:
                    tool_results = [
                        {
                            "name": pending_tool_call.name,
                            "result": {
                                "success": False,
                                "cancelled": True,
                                "reason": "User rejected the action.",
                            },
                        }
                    ]

                    await self.conversation_store.clear_pending_tool_call(
                        conversation_id
                    )

                    response = await self.ai_client.chat_with_tool_results(
                        previous_response=previous_response,
                        tool_results=tool_results,
                        tools=tool_definitions,
                    )

                else:
                    tool = self.tools.get(pending_tool_call.name)

                    if not tool:
                        raise ValueError(f"Unknown tool: {pending_tool_call.name}")

                    tool_call_count += 1
                    if tool_call_count > self.MAX_TOOL_CALLS_PER_REQUEST:
                        raise ValueError(
                            "Maximum number of tool calls per request exceeded "
                            f"({self.MAX_TOOL_CALLS_PER_REQUEST})."
                        )

                    arguments = tool.input_model.model_validate(
                        pending_tool_call.arguments
                    )

                    tool_calls.append(tool.name)

                    tool_result = await tool.execute(**arguments.model_dump())

                    await self.conversation_store.clear_pending_tool_call(
                        conversation_id
                    )

                    response = await self.ai_client.chat_with_tool_results(
                        previous_response=previous_response,
                        tool_results=[
                            {
                                "name": tool.name,
                                "result": tool_result,
                            }
                        ],
                        tools=tool_definitions,
                    )

            else:
                response = await self.ai_client.chat(
                    message=message,
                    tools=tool_definitions,
                    state=state,
                )

            for _ in range(self.MAX_AGENT_STEPS):
                if not response.tool_calls:
                    await self._save_state(
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

                batch_size = len(response.tool_calls)
                if batch_size > self.MAX_TOOL_CALLS_PER_BATCH:
                    raise ValueError(
                        "Maximum number of tool calls per batch exceeded "
                        f"({self.MAX_TOOL_CALLS_PER_BATCH})."
                    )

                if tool_call_count + batch_size > self.MAX_TOOL_CALLS_PER_REQUEST:
                    raise ValueError(
                        "Maximum number of tool calls per request exceeded "
                        f"({self.MAX_TOOL_CALLS_PER_REQUEST})."
                    )

                tools_for_calls = []
                for tool_call in response.tool_calls:
                    tool = self.tools.get(tool_call.name)
                    if not tool:
                        raise ValueError(f"Unknown tool: {tool_call.name}")
                    tools_for_calls.append((tool_call, tool))

                if len(tools_for_calls) > 1 and any(
                    getattr(tool, "requires_confirmation", False)
                    for _, tool in tools_for_calls
                ):
                    raise ValueError(
                        "Multiple tool calls containing write actions are not "
                        "supported."
                    )

                tool_call_count += batch_size
                tool_results = []
                for tool_call, tool in tools_for_calls:
                    tool_calls.append(tool.name)

                    try:
                        arguments = tool.input_model.model_validate(tool_call.arguments)
                    except ValidationError as exc:
                        tool_results.append(
                            {
                                "name": tool.name,
                                "result": {
                                    "success": False,
                                    "error": {
                                        "type": "validation_error",
                                        "details": exc.errors(
                                            include_url=False,
                                            include_input=False,
                                        ),
                                    },
                                },
                            }
                        )
                        continue

                    if getattr(tool, "requires_confirmation", False):
                        await self.conversation_store.save_pending_tool_call(
                            conversation_id=conversation_id,
                            tool_call=PendingToolCall(
                                name=tool.name,
                                arguments=arguments.model_dump(),
                            ),
                        )

                        await self._save_state(
                            conversation_id=conversation_id,
                            state=response.state,
                        )

                        return (
                            "Please confirm that you want to execute "
                            f"{tool.name} with "
                            f"{arguments.model_dump()}."
                        )

                    tool_result = await tool.execute(**arguments.model_dump())
                    tool_results.append(
                        {
                            "name": tool.name,
                            "result": tool_result,
                        }
                    )

                response = await self.ai_client.chat_with_tool_results(
                    previous_response=response,
                    tool_results=tool_results,
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

    async def _save_state(
        self,
        conversation_id: str,
        state,
    ) -> None:
        serialized_state = self.ai_client.serialize_state(state)

        await self.conversation_store.save(
            conversation_id,
            serialized_state,
        )
