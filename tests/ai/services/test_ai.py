from typing import ClassVar

import pytest

from app.ai.models import LLMResponse, PendingToolCall, ToolCall
from app.ai.tools.schemas import GetOrderStatusInput, SearchProductsInput
from app.core.dependencies.ai import get_ai_client
from app.services.ai.ai import AIService


class FakeConversationStore:
    def __init__(
        self,
        stored_state=None,
    ):
        self.stored_state = stored_state
        self.saved_state = None
        self.pending_tool_call = None

    async def get(
        self,
        conversation_id: str,
    ):
        return self.stored_state

    async def save(
        self,
        conversation_id: str,
        state,
    ):
        self.saved_state = state

    async def get_pending_tool_call(
        self,
        conversation_id: str,
    ):
        return self.pending_tool_call

    async def save_pending_tool_call(
        self,
        conversation_id: str,
        tool_call,
    ):
        self.pending_tool_call = tool_call

    async def clear_pending_tool_call(
        self,
        conversation_id: str,
    ):
        self.pending_tool_call = None


class FakeSearchProductsTool:
    name = "search_products"
    input_model = SearchProductsInput

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
        self.execution_count = 0

    async def execute(
        self,
        query: str,
        min_price: float | None = None,
        max_price: float | None = None,
    ):
        self.was_called = True
        self.execution_count += 1
        self.arguments = {
            "query": query,
            "min_price": min_price,
            "max_price": max_price,
        }

        return self.result


class FakeGetOrderStatusTool:
    name = "get_order_status"
    input_model = GetOrderStatusInput

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

    async def execute(self, order_id: int):
        self.was_called = True
        self.order_id = order_id

        return {
            "order_id": order_id,
            "status": "processing",
        }


class SingleToolAIClient:
    def __init__(self):
        self.tool_results = None
        self.received_state = None

    async def chat(
        self,
        message: str,
        tools=None,
        state=None,
    ) -> LLMResponse:
        self.received_state = state

        return LLMResponse(
            tool_calls=[
                ToolCall(
                    name="search_products",
                    arguments={
                        "query": "wireless headphones",
                        "max_price": 150,
                    },
                )
            ],
            state=["tool-call-state"],
        )

    async def chat_with_tool_results(
        self,
        previous_response: LLMResponse,
        tool_results,
        tools=None,
    ) -> LLMResponse:
        self.tool_results = tool_results

        return LLMResponse(
            content="I recommend the Quiet Headphones.",
            state=["final-state"],
        )

    def serialize_state(self, state):
        return state

    def deserialize_state(self, state):
        return state


class EmptyResultAIClient(SingleToolAIClient):
    async def chat_with_tool_results(
        self,
        previous_response: LLMResponse,
        tool_results,
        tools=None,
    ) -> LLMResponse:
        self.tool_results = tool_results

        return LLMResponse(
            content="I couldn't find any matching products.",
            state=["final-state"],
        )


class MultiToolAIClient:
    def __init__(self):
        self.calls = 0

    async def chat(
        self,
        message: str,
        tools=None,
        state=None,
    ) -> LLMResponse:
        return LLMResponse(
            tool_calls=[
                ToolCall(
                    name="search_products",
                    arguments={
                        "query": "headphones",
                        "max_price": 100,
                    },
                ),
                ToolCall(
                    name="get_order_status",
                    arguments={"order_id": 42},
                ),
            ],
            state=["search-state"],
        )

    async def chat_with_tool_results(
        self,
        previous_response: LLMResponse,
        tool_results,
        tools=None,
    ) -> LLMResponse:
        self.calls += 1
        self.tool_results = tool_results

        return LLMResponse(
            content=("I found matching headphones and order 42 is processing."),
            state=["final-state"],
        )

    def serialize_state(self, state):
        return state

    def deserialize_state(self, state):
        return state


class UnknownToolAIClient:
    async def chat(
        self,
        message: str,
        tools=None,
        state=None,
    ) -> LLMResponse:
        return LLMResponse(
            tool_calls=[
                ToolCall(
                    name="non_existing_tool",
                    arguments={},
                )
            ],
            state=["tool-call-state"],
        )

    def serialize_state(self, state):
        return state

    def deserialize_state(self, state):
        return state


class EndlessToolAIClient:
    async def chat(
        self,
        message: str,
        tools=None,
        state=None,
    ) -> LLMResponse:
        return LLMResponse(
            tool_calls=[
                ToolCall(
                    name="search_products",
                    arguments={
                        "query": "headphones",
                    },
                )
            ],
            state=["state"],
        )

    async def chat_with_tool_results(
        self,
        previous_response: LLMResponse,
        tool_results,
        tools=None,
    ) -> LLMResponse:
        return LLMResponse(
            tool_calls=[
                ToolCall(
                    name="search_products",
                    arguments={
                        "query": "headphones",
                    },
                )
            ],
            state=["state"],
        )

    def serialize_state(self, state):
        return state

    def deserialize_state(self, state):
        return state


class FailingSearchProductsTool(FakeSearchProductsTool):
    async def execute(
        self,
        query: str,
        min_price: float | None = None,
        max_price: float | None = None,
    ):
        raise RuntimeError("Product search failed")


class InvalidToolArgumentsAIClient:
    async def chat(
        self,
        message: str,
        tools=None,
        state=None,
    ) -> LLMResponse:
        return LLMResponse(
            tool_calls=[
                ToolCall(
                    name="get_order_status",
                    arguments={
                        "order_id": -5,
                    },
                )
            ],
            state=["tool-call-state"],
        )

    async def chat_with_tool_results(
        self,
        previous_response: LLMResponse,
        tool_results,
        tools=None,
    ) -> LLMResponse:
        return LLMResponse(
            content="The order ID is invalid.",
            state=["final-state"],
        )

    def serialize_state(self, state):
        return state

    def deserialize_state(self, state):
        return state


class RecoveringAIClient:
    def __init__(self):
        self.tool_results = None
        self.calls = 0

    async def chat(
        self,
        message: str,
        tools=None,
        state=None,
    ) -> LLMResponse:
        return LLMResponse(
            tool_calls=[
                ToolCall(
                    name="get_order_status",
                    arguments={
                        "order_id": -5,
                    },
                )
            ],
            state=["invalid-tool-state"],
        )

    async def chat_with_tool_results(
        self,
        previous_response: LLMResponse,
        tool_results,
        tools=None,
    ) -> LLMResponse:
        self.calls += 1
        self.tool_results = tool_results

        if self.calls == 1:
            return LLMResponse(
                tool_calls=[
                    ToolCall(
                        name="get_order_status",
                        arguments={
                            "order_id": 42,
                        },
                    )
                ],
                state=["corrected-tool-state"],
            )

        return LLMResponse(
            content="Order 42 is processing.",
            state=["final-state"],
        )

    def serialize_state(self, state):
        return state

    def deserialize_state(self, state):
        return state


class ConfirmableTool:
    name = "cancel_order"
    requires_confirmation = True
    input_model = GetOrderStatusInput

    definition: ClassVar[dict] = {
        "name": name,
        "description": "Cancel an order.",
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
        self.received_order_id = None

    async def execute(
        self,
        order_id: int,
    ):
        self.was_called = True
        self.received_order_id = order_id

        return {
            "success": True,
            "order_id": order_id,
        }


class ConfirmableToolAIClient:
    async def chat(
        self,
        message,
        tools=None,
        state=None,
    ):
        return LLMResponse(
            tool_calls=[
                ToolCall(
                    name="cancel_order",
                    arguments={"order_id": 42},
                )
            ],
            state=["tool-call-state"],
        )

    async def chat_with_tool_results(
        self,
        previous_response,
        tool_results,
        tools=None,
    ):
        self.received_tool_results = tool_results

        return LLMResponse(
            content="Action handled.",
            state=["final-state"],
        )

    def serialize_state(self, state):
        return state

    def deserialize_state(self, state):
        return state


class MixedToolAIClient:
    async def chat(
        self,
        message,
        tools=None,
        state=None,
    ):
        return LLMResponse(
            tool_calls=[
                ToolCall(
                    name="search_products",
                    arguments={"query": "laptop"},
                ),
                ToolCall(
                    name="cancel_order",
                    arguments={"order_id": 42},
                ),
            ],
            state=["mixed-tool-call-state"],
        )

    def serialize_state(self, state):
        return state

    def deserialize_state(self, state):
        return state


class RepeatingBatchAIClient:
    def __init__(self, batch_size: int, batches: int):
        self.batch_size = batch_size
        self.batches = batches
        self.completed_batches = 0

    def _tool_response(self):
        return LLMResponse(
            tool_calls=[
                ToolCall(
                    name="search_products",
                    arguments={"query": f"query-{index}"},
                )
                for index in range(self.batch_size)
            ],
            state=["tool-call-state"],
        )

    async def chat(self, message, tools=None, state=None):
        return self._tool_response()

    async def chat_with_tool_results(
        self,
        previous_response,
        tool_results,
        tools=None,
    ):
        self.completed_batches += 1
        if self.completed_batches < self.batches:
            return self._tool_response()
        return LLMResponse(content="Finished.", state=["final-state"])

    def serialize_state(self, state):
        return state

    def deserialize_state(self, state):
        return state


@pytest.mark.anyio
async def test_ai_service_passes_empty_tool_result_to_llm():
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

    answer = await service.chat(
        message="Find headphones",
        conversation_id="conversation-1",
    )

    assert search_tool.was_called
    assert ai_client.tool_results == [
        {
            "name": "search_products",
            "result": [],
        }
    ]

    assert conversation_store.saved_state == ["final-state"]

    assert answer == ("I couldn't find any matching products.")


@pytest.mark.anyio
async def test_ai_service_executes_multiple_tools():
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

    answer = await service.chat(
        message=("Find headphones under 100 EUR and tell me the status of order 42"),
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
    assert ai_client.calls == 1
    assert [result["name"] for result in ai_client.tool_results] == [
        "search_products",
        "get_order_status",
    ]

    assert conversation_store.saved_state == ["final-state"]

    assert answer == ("I found matching headphones and order 42 is processing.")


@pytest.mark.anyio
async def test_ai_service_rejects_batch_containing_write_action():
    ai_client = MixedToolAIClient()
    conversation_store = FakeConversationStore()
    search_tool = FakeSearchProductsTool()
    cancel_tool = ConfirmableTool()

    service = AIService(
        ai_client=ai_client,
        conversation_store=conversation_store,
        tools=[search_tool, cancel_tool],
    )

    with pytest.raises(
        ValueError,
        match="Multiple tool calls containing write actions are not supported",
    ):
        await service.chat(
            message="Find a laptop and cancel order 42",
            conversation_id="mixed-read-write-tools",
        )

    assert search_tool.was_called is False
    assert cancel_tool.was_called is False
    assert conversation_store.pending_tool_call is None


@pytest.mark.anyio
async def test_ai_service_limits_tool_calls_per_batch_before_execution():
    ai_client = RepeatingBatchAIClient(
        batch_size=AIService.MAX_TOOL_CALLS_PER_BATCH + 1,
        batches=1,
    )
    search_tool = FakeSearchProductsTool()
    service = AIService(
        ai_client=ai_client,
        conversation_store=FakeConversationStore(),
        tools=[search_tool],
    )

    with pytest.raises(
        ValueError,
        match="Maximum number of tool calls per batch exceeded \\(5\\)",
    ):
        await service.chat("Search repeatedly", "tool-batch-limit")

    assert search_tool.execution_count == 0


@pytest.mark.anyio
async def test_ai_service_limits_total_tool_calls_per_request():
    batch_size = AIService.MAX_TOOL_CALLS_PER_BATCH
    ai_client = RepeatingBatchAIClient(
        batch_size=batch_size,
        batches=3,
    )
    search_tool = FakeSearchProductsTool()
    service = AIService(
        ai_client=ai_client,
        conversation_store=FakeConversationStore(),
        tools=[search_tool],
    )

    with pytest.raises(
        ValueError,
        match="Maximum number of tool calls per request exceeded \\(10\\)",
    ):
        await service.chat("Search repeatedly", "tool-request-limit")

    assert search_tool.execution_count == AIService.MAX_TOOL_CALLS_PER_REQUEST


@pytest.mark.anyio
async def test_ai_service_loads_existing_conversation_state():
    stored_state = ["previous-conversation-state"]

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

    await service.chat(
        message="42",
        conversation_id="conversation-1",
    )

    assert ai_client.received_state == stored_state


@pytest.mark.anyio
async def test_ai_service_raises_for_unknown_tool():
    ai_client = UnknownToolAIClient()
    conversation_store = FakeConversationStore()

    service = AIService(
        ai_client=ai_client,
        conversation_store=conversation_store,
        tools=[
            FakeSearchProductsTool(),
        ],
    )

    with pytest.raises(
        ValueError,
        match="Unknown tool: non_existing_tool",
    ):
        await service.chat(
            message="Do something",
            conversation_id="conversation-1",
        )


@pytest.mark.anyio
async def test_ai_service_stops_after_max_agent_steps():
    ai_client = EndlessToolAIClient()
    conversation_store = FakeConversationStore()

    service = AIService(
        ai_client=ai_client,
        conversation_store=conversation_store,
        tools=[
            FakeSearchProductsTool(),
        ],
    )

    with pytest.raises(
        RuntimeError,
        match="Maximum number of agent steps exceeded",
    ):
        await service.chat(
            message="Keep searching",
            conversation_id="conversation-1",
        )


@pytest.mark.anyio
async def test_ai_service_propagates_tool_exception():
    ai_client = SingleToolAIClient()
    conversation_store = FakeConversationStore()

    service = AIService(
        ai_client=ai_client,
        conversation_store=conversation_store,
        tools=[
            FailingSearchProductsTool(),
        ],
    )

    with pytest.raises(
        RuntimeError,
        match="Product search failed",
    ):
        await service.chat(
            message="Find headphones",
            conversation_id="conversation-1",
        )

    assert conversation_store.saved_state is None


@pytest.mark.anyio
async def test_ai_service_does_not_execute_tool_with_invalid_arguments():
    ai_client = InvalidToolArgumentsAIClient()
    conversation_store = FakeConversationStore()
    order_tool = FakeGetOrderStatusTool()

    service = AIService(
        ai_client=ai_client,
        conversation_store=conversation_store,
        tools=[order_tool],
    )

    answer = await service.chat(
        message="Check order",
        conversation_id="conversation-1",
    )

    assert not order_tool.was_called

    assert answer == "The order ID is invalid."

    assert conversation_store.saved_state == ["final-state"]


@pytest.mark.anyio
async def test_ai_service_recovers_from_invalid_tool_arguments():
    ai_client = RecoveringAIClient()
    conversation_store = FakeConversationStore()
    order_tool = FakeGetOrderStatusTool()

    service = AIService(
        ai_client=ai_client,
        conversation_store=conversation_store,
        tools=[order_tool],
    )

    answer = await service.chat(
        message="Check my order",
        conversation_id="conversation-1",
    )

    assert order_tool.was_called
    assert order_tool.order_id == 42

    assert answer == "Order 42 is processing."

    assert conversation_store.saved_state == ["final-state"]


@pytest.mark.anyio
async def test_ai_service_does_not_execute_tool_without_confirmation():
    ai_client = ConfirmableToolAIClient()
    conversation_store = FakeConversationStore()
    tool = ConfirmableTool()

    service = AIService(
        ai_client=ai_client,
        conversation_store=conversation_store,
        tools=[tool],
    )

    answer = await service.chat(
        message="Cancel order 42",
        conversation_id="conversation-1",
    )

    assert tool.was_called is False

    assert conversation_store.pending_tool_call == PendingToolCall(
        name="cancel_order",
        arguments={"order_id": 42},
    )

    assert conversation_store.saved_state == ["tool-call-state"]

    assert "Please confirm" in answer


@pytest.mark.anyio
async def test_ai_service_executes_pending_tool_when_confirmed():
    ai_client = ConfirmableToolAIClient()

    conversation_store = FakeConversationStore(
        stored_state=["tool-call-state"],
    )

    conversation_store.pending_tool_call = PendingToolCall(
        name="cancel_order",
        arguments={"order_id": 42},
    )

    tool = ConfirmableTool()

    service = AIService(
        ai_client=ai_client,
        conversation_store=conversation_store,
        tools=[tool],
    )

    answer = await service.chat(
        message="",
        conversation_id="conversation-1",
        confirm_action=True,
    )

    assert tool.was_called is True
    assert tool.received_order_id == 42

    assert conversation_store.pending_tool_call is None

    assert conversation_store.saved_state == ["final-state"]

    assert answer == "Action handled."


@pytest.mark.anyio
async def test_ai_service_does_not_execute_pending_tool_when_rejected():
    ai_client = ConfirmableToolAIClient()

    conversation_store = FakeConversationStore(
        stored_state=["tool-call-state"],
    )

    conversation_store.pending_tool_call = PendingToolCall(
        name="cancel_order",
        arguments={"order_id": 42},
    )

    tool = ConfirmableTool()

    service = AIService(
        ai_client=ai_client,
        conversation_store=conversation_store,
        tools=[tool],
    )

    await service.chat(
        message="",
        conversation_id="conversation-1",
        confirm_action=False,
    )

    assert tool.was_called is False
    assert conversation_store.pending_tool_call is None

    assert conversation_store.saved_state == ["final-state"]


def test_ai_client_is_reused():
    first = get_ai_client()
    second = get_ai_client()

    assert first is second
