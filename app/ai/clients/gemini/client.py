from google import genai
from google.genai import types

from app.ai.clients.llm_base import LLMClient
from app.ai.clients.gemini.helper import with_retry
from app.ai.models import LLMResponse, ToolCall
from app.core.config import settings


class GeminiClient(LLMClient):
    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.gemini_api_key,
        )

    def chat(
        self,
        message: str
    ) -> LLMResponse:
        def request():
            tool_definitions = [
                tool.definition
                for tool in self.tools.values()
            ]

            response = self.ai_client.chat(
                message,
                tools=tool_definitions,
            )

            max_steps = 5

            for _ in range(max_steps):
                if not response.tool_call:
                    return response.content or ""

                tool = self.tools.get(response.tool_call.name)

                if not tool:
                    raise ValueError(
                        f"Unknown tool: {response.tool_call.name}"
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


    def chat_with_tool_result(
        self,
        previous_response: LLMResponse,
        tool_result: list[dict],
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        def request():
            gemini_tools = None

            if tools:
                gemini_tools = [
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


            tool_call = previous_response.tool_call

            function_response = types.Content(
                role="user",
                parts=[
                    types.Part.from_function_response(
                        name=tool_call.name,
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
                model="gemini-3.6-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "You are an assistant for an e-commerce application. "
                        "Use tool results when needed. "
                        "Do not invent products, prices, stock, "
                        "order information, or features."
                    ),
                    tools=gemini_tools,
                ),
            )

            state = [
                *contents,
                response.candidates[0].content,
            ]   

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

        return with_retry(request)