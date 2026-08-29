from app.ai.clients.llm_base import LLMClient


class AIService:
    MAX_AGENT_STEPS = 5

    def __init__(
        self,
        ai_client: LLMClient,
        tools: list,
    ):
        self.ai_client = ai_client
        self.tools = {
            tool.name: tool
            for tool in tools
        }

    def chat(self, message: str) -> str:
        tool_definitions = [
            tool.definition
            for tool in self.tools.values()
        ]

        response = self.ai_client.chat(
            message,
            tools=tool_definitions,
        )

        for _ in range(self.MAX_AGENT_STEPS):
            if not response.tool_call:
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