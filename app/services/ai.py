import time

from pydantic import ValidationError

from app.ai.clients.llm_base import LLMClient
from app.ai.conversation.store import ConversationStore
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
        self.tools = {
            tool.name: tool
            for tool in tools
        }

    def chat(
        self,
        message: str,
        conversation_id: str,
    ) -> str:
        start_time = time.perf_counter()
        tool_calls: list[str] = []

        try:
            tool_definitions = [
                tool.definition
                for tool in self.tools.values()
            ]

            stored_state = self.conversation_store.get(
                conversation_id
            )

            state = None

            if stored_state is not None:
                state = self.ai_client.deserialize_state(
                    stored_state
                )

            response = self.ai_client.chat(
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

                tool_calls.append(
                    response.tool_call.name
                )

                tool = self.tools.get(
                    response.tool_call.name
                )

                if not tool:
                    raise ValueError(
                        f"Unknown tool: "
                        f"{response.tool_call.name}"
                    )

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

                    response = self.ai_client.chat_with_tool_result(
                        previous_response=response,
                        tool_result=tool_result,
                        tools=tool_definitions,
                    )

                    continue

                tool_result = tool.execute(
                    **arguments.model_dump()
                )

                response = self.ai_client.chat_with_tool_result(
                    previous_response=response,
                    tool_result=tool_result,
                    tools=tool_definitions,
                )

            raise RuntimeError(
                "Maximum number of agent steps exceeded."
            )

        except Exception:
            logger.exception(
                "ai_request_failed",
                extra={
                    "conversation_id": conversation_id,
                    "duration_ms": round(
                        (time.perf_counter() - start_time) * 1000,
                        2,
                    ),
                    "tool_calls": tool_calls
                },
            )
            raise

    def _save_state(
        self,
        conversation_id: str,
        state,
    ) -> None:
        serialized_state = self.ai_client.serialize_state(
            state
        )

        self.conversation_store.save(
            conversation_id,
            serialized_state,
        )