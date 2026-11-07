from types import SimpleNamespace

import pytest
from google.genai import types

from app.ai.clients.gemini.client import GeminiClient
from app.ai.models import LLMResponse, ToolCall


def test_gemini_response_preserves_all_function_calls():
    client = object.__new__(GeminiClient)
    response = SimpleNamespace(
        function_calls=[
            SimpleNamespace(
                name="search_products",
                args={"query": "laptop"},
            ),
            SimpleNamespace(
                name="get_order_status",
                args={"order_id": 12},
            ),
        ],
        text=None,
    )

    result = client._to_response(response, state=["model-state"])

    assert result.tool_calls == [
        ToolCall(name="search_products", arguments={"query": "laptop"}),
        ToolCall(name="get_order_status", arguments={"order_id": 12}),
    ]
    assert result.state == ["model-state"]


@pytest.mark.asyncio
async def test_gemini_sends_all_tool_results_in_one_function_response():
    class FakeModels:
        def __init__(self):
            self.request = None

        async def generate_content(self, **request):
            self.request = request
            return SimpleNamespace(
                candidates=[
                    SimpleNamespace(
                        content=types.Content(
                            role="model",
                            parts=[types.Part.from_text(text="Combined answer.")],
                        )
                    )
                ],
                function_calls=None,
                text="Combined answer.",
                usage_metadata=None,
            )

    models = FakeModels()
    client = object.__new__(GeminiClient)
    client.model = "test-model"
    client.client = SimpleNamespace(
        aio=SimpleNamespace(models=models),
    )
    client._log_completed_call = lambda **_: None

    result = await client.chat_with_tool_results(
        previous_response=LLMResponse(
            tool_calls=[
                ToolCall(name="search_products", arguments={"query": "laptop"}),
                ToolCall(name="get_order_status", arguments={"order_id": 12}),
            ],
            state=[
                types.Content(
                    role="model",
                    parts=[types.Part.from_text(text="Tool requests")],
                )
            ],
        ),
        tool_results=[
            {
                "name": "search_products",
                "result": [{"name": "Laptop"}],
            },
            {
                "name": "get_order_status",
                "result": {"status": "shipped"},
            },
        ],
    )

    function_responses = models.request["contents"][-1].parts
    assert [part.function_response.name for part in function_responses] == [
        "search_products",
        "get_order_status",
    ]
    assert [
        part.function_response.response["result"] for part in function_responses
    ] == [
        [{"name": "Laptop"}],
        {"status": "shipped"},
    ]
    assert result.content == "Combined answer."
