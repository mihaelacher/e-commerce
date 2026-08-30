from app.ai.clients.llm_base import LLMClient
from app.ai.conversation.store import ConversationStore


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

                return response.content or ""

            tool = self.tools.get(
                response.tool_call.name
            )

            if not tool:
                raise ValueError(
                    f"Unknown tool: "
                    f"{response.tool_call.name}"
                )

            tool_result = tool.execute(
                **response.tool_call.arguments
            )

            response = self.ai_client.chat_with_tool_result(
                previous_response=response,
                tool_result=tool_result,
                tools=tool_definitions,
            )

        raise RuntimeError(
            "Maximum number of agent steps exceeded."
        )

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