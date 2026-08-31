from app.ai.models import LLMResponse, ToolCall
from app.services.ai import AIService


class FakeConversationStore:
    def __init__(self, stored_state=None):
        self.stored_state = stored_state
        self.saved_conversation_id = None
        self.saved_state = None

    def get(self, conversation_id: str):
        return self.stored_state

    def save(
        self,
        conversation_id: str,
        state,
    ) -> None:
        self.saved_conversation_id = conversation_id
        self.saved_state = state


class FakeSearchProductsTool:
    name = "search_products"

    def __init__(self, result=None):
        self.definition = {
            "name": self.name,
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

    def __init__(self):
        self.definition = {
            "name": self.name,
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
        self.received_state = None

    def chat(
        self,
        message: str,
        tools=None,
        state=None,
    ) -> LLMResponse:
        self.received_state = state

        return LLMResponse(
            tool_call=ToolCall(
                name="search_products",
                arguments={
                    "query": "wireless headphones",
                    "max_price": 150,
                },
            ),
            state=["tool-call-state"],
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
            state=["final-state"],
        )

    def serialize_state(self, state):
        return state

    def deserialize_state(self, state):
        return state


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
            state=["final-state"],
        )


class MultiToolAIClient:
    def __init__(self):
        self.calls = 0

    def chat(
        self,
        message: str,
        tools=None,
        state=None,
    ) -> LLMResponse:
        return LLMResponse(
            tool_call=ToolCall(
                name="search_products",
                arguments={
                    "query": "headphones",
                    "max_price": 100,
                },
            ),
            state=["search-state"],
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
                state=["order-state"],
            )

        return LLMResponse(
            content=(
                "I found matching headphones and "
                "order 42 is processing."
            ),
            state=["final-state"],
        )

    def serialize_state(self, state):
        return state

    def deserialize_state(self, state):
        return state


def test_ai_service_passes_empty_tool_result_to_llm():
    ai_client = EmptyResultAIClient()
    conversation_store = FakeConversationStore()

    search_tool = FakeSearchProductsTool(
        result=[],
    )

    service = AIService(
        ai_client=ai_client,
        conversation_store=conversation_store,
        tools=[search_tool],
    )

    answer = service.chat(
        message="Find headphones",
        conversation_id="conversation-1",
    )

    assert search_tool.was_called
    assert ai_client.tool_result == []

    assert conversation_store.saved_state == [
        "final-state"
    ]

    assert answer == (
        "I couldn't find any matching products."
    )


def test_ai_service_executes_multiple_tools():
    ai_client = MultiToolAIClient()
    conversation_store = FakeConversationStore()

    search_tool = FakeSearchProductsTool()
    order_tool = FakeGetOrderStatusTool()

    service = AIService(
        ai_client=ai_client,
        conversation_store=conversation_store,
        tools=[
            search_tool,
            order_tool,
        ],
    )

    answer = service.chat(
        message=(
            "Find headphones under 100 EUR "
            "and tell me the status of order 42"
        ),
        conversation_id="conversation-1",
    )

    assert search_tool.was_called

    assert search_tool.arguments == {
        "query": "headphones",
        "min_price": None,
        "max_price": 100,
    }

    assert order_tool.was_called
    assert order_tool.order_id == 42

    assert conversation_store.saved_state == [
        "final-state"
    ]

    assert answer == (
        "I found matching headphones and "
        "order 42 is processing."
    )


def test_ai_service_loads_existing_conversation_state():
    stored_state = [
        "previous-conversation-state"
    ]

    ai_client = SingleToolAIClient()

    conversation_store = FakeConversationStore(
        stored_state=stored_state,
    )

    search_tool = FakeSearchProductsTool()

    service = AIService(
        ai_client=ai_client,
        conversation_store=conversation_store,
        tools=[search_tool],
    )

    service.chat(
        message="42",
        conversation_id="conversation-1",
    )

    assert ai_client.received_state == stored_state            