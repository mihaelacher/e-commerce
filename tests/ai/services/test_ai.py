from app.ai.models import LLMResponse, ToolCall
from app.services.ai import AIService


class FakeSearchProductsTool:
    name = "search_products"

    definition = {
        "name": name,
        "description": "Search products.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "min_price": {"type": "number"},
                "max_price": {"type": "number"},
            },
            "required": ["query"],
        },
    }

    def __init__(self, result=None):
        self.result = result or []
        self.was_called = False
        self.arguments = None

    def execute(
        self,
        query: str,
        min_price: float | None = None,
        max_price: float | None = None,
    ):
        self.was_called = True
        self.arguments = {
            "query": query,
            "min_price": min_price,
            "max_price": max_price,
        }

        return self.result


class FakeGetOrderStatusTool:
    name = "get_order_status"

    definition = {
        "name": name,
        "description": "Get the current status of an order.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                },
            },
            "required": ["order_id"],
        },
    }

    def __init__(self):
        self.was_called = False
        self.order_id = None

    def execute(self, order_id: int):
        self.was_called = True
        self.order_id = order_id

        return {
            "order_id": order_id,
            "status": "processing",
        }


class SingleToolAIClient:
    def __init__(self):
        self.tool_result = None

    def chat(
        self,
        message: str,
        tools=None,
    ) -> LLMResponse:
        return LLMResponse(
            tool_call=ToolCall(
                name="search_products",
                arguments={
                    "query": "wireless headphones",
                    "max_price": 150,
                },
            ),
            state=[],
        )

    def chat_with_tool_result(
        self,
        previous_response: LLMResponse,
        tool_result,
        tools=None,
    ) -> LLMResponse:
        self.tool_result = tool_result

        return LLMResponse(
            content="I recommend the Quiet Headphones.",
            state=[],
        )


class EmptyResultAIClient(SingleToolAIClient):
    def chat_with_tool_result(
        self,
        previous_response: LLMResponse,
        tool_result,
        tools=None,
    ) -> LLMResponse:
        self.tool_result = tool_result

        return LLMResponse(
            content="I couldn't find any matching products.",
            state=[],
        )


class MultiToolAIClient:
    def __init__(self):
        self.calls = 0

    def chat(
        self,
        message: str,
        tools=None,
    ) -> LLMResponse:
        return LLMResponse(
            tool_call=ToolCall(
                name="search_products",
                arguments={
                    "query": "headphones",
                    "max_price": 100,
                },
            ),
            state=[],
        )

    def chat_with_tool_result(
        self,
        previous_response: LLMResponse,
        tool_result,
        tools=None,
    ) -> LLMResponse:
        self.calls += 1

        if self.calls == 1:
            return LLMResponse(
                tool_call=ToolCall(
                    name="get_order_status",
                    arguments={
                        "order_id": 42,
                    },
                ),
                state=[],
            )

        return LLMResponse(
            content=(
                "I found matching headphones and "
                "order 42 is processing."
            ),
            state=[],
        )


def test_ai_service_executes_search_tool():
    tool_result = [
        {
            "name": "Quiet Headphones",
            "price": "99.99",
            "stock": 3,
            "description": "Noise cancelling",
        }
    ]

    ai_client = SingleToolAIClient()

    search_tool = FakeSearchProductsTool(
        result=tool_result,
    )

    service = AIService(
        ai_client=ai_client,
        tools=[search_tool],
    )

    answer = service.chat(
        "I need wireless headphones under 150 EUR"
    )

    assert search_tool.was_called

    assert search_tool.arguments == {
        "query": "wireless headphones",
        "min_price": None,
        "max_price": 150,
    }

    assert ai_client.tool_result == tool_result

    assert answer == "I recommend the Quiet Headphones."


def test_ai_service_passes_empty_tool_result_to_llm():
    ai_client = EmptyResultAIClient()

    search_tool = FakeSearchProductsTool(
        result=[],
    )

    service = AIService(
        ai_client=ai_client,
        tools=[search_tool],
    )

    answer = service.chat("Find headphones")

    assert search_tool.was_called
    assert ai_client.tool_result == []

    assert answer == (
        "I couldn't find any matching products."
    )


def test_ai_service_executes_multiple_tools():
    ai_client = MultiToolAIClient()

    search_tool = FakeSearchProductsTool()
    order_tool = FakeGetOrderStatusTool()

    service = AIService(
        ai_client=ai_client,
        tools=[
            search_tool,
            order_tool,
        ],
    )

    answer = service.chat(
        "Find headphones under 100 EUR "
        "and tell me the status of order 42"
    )

    assert search_tool.was_called

    assert search_tool.arguments == {
        "query": "headphones",
        "min_price": None,
        "max_price": 100,
    }

    assert order_tool.was_called
    assert order_tool.order_id == 42

    assert answer == (
        "I found matching headphones and "
        "order 42 is processing."
    )