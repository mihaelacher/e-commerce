import uuid

import pytest
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.ai.tools.schemas import (
    CancelOrderInput,
    GetOrderStatusInput,
    SearchKnowledgeInput,
    SearchProductsInput,
)
from app.services.ai.langgraph_ai import LangGraphAIService


class FakeTool:
    def __init__(self, name, input_model, result=None):
        self.name = name
        self.input_model = input_model
        self.definition = {"description": name}
        self.result = result or []
        self.calls = []

    async def execute(self, **arguments):
        self.calls.append(arguments)
        return self.result


class FakeLLM:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def bind_tools(self, tools):
        self.tools = tools
        return self

    async def ainvoke(self, messages):
        self.calls += 1
        return self.responses.pop(0)


def build_service(llm, cancel_tool):
    return LangGraphAIService(
        llm=llm,
        search_products_tool=FakeTool(
            "search_products",
            SearchProductsInput,
        ),
        search_knowledge_tool=FakeTool(
            "search_knowledge",
            SearchKnowledgeInput,
        ),
        get_order_status_tool=FakeTool(
            "get_order_status",
            GetOrderStatusInput,
        ),
        cancel_order_tool=cancel_tool,
        checkpointer=InMemorySaver(),
    )


@pytest.mark.anyio
async def test_langgraph_returns_final_answer():
    service = build_service(
        FakeLLM([AIMessage(content="Hello from the assistant.")]),
        FakeTool("cancel_order", CancelOrderInput),
    )

    result = await service.chat(
        message="Hello",
        conversation_id="final-answer",
    )

    assert result.answer == "Hello from the assistant."
    assert result.conversation_id == "final-answer"
    assert result.requires_confirmation is False


@pytest.mark.anyio
async def test_langgraph_executes_multiple_read_tools():
    products_tool = FakeTool(
        "search_products",
        SearchProductsInput,
        result=[{"name": "Laptop"}],
    )
    order_status_tool = FakeTool(
        "get_order_status",
        GetOrderStatusInput,
        result={"status": "shipped"},
    )
    service = LangGraphAIService(
        llm=FakeLLM(
            [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "search_products",
                            "args": {"query": "products"},
                            "id": "products-1",
                            "type": "tool_call",
                        },
                        {
                            "name": "get_order_status",
                            "args": {"order_id": 12},
                            "id": "order-status-1",
                            "type": "tool_call",
                        },
                    ],
                ),
                AIMessage(content="Here are products; order 12 shipped."),
            ]
        ),
        search_products_tool=products_tool,
        search_knowledge_tool=FakeTool(
            "search_knowledge",
            SearchKnowledgeInput,
        ),
        get_order_status_tool=order_status_tool,
        cancel_order_tool=FakeTool("cancel_order", CancelOrderInput),
        checkpointer=InMemorySaver(),
    )

    result = await service.chat(
        message="What products do you have and what is the status of order 12?",
        conversation_id="multiple-read-tools",
    )

    assert result.answer == "Here are products; order 12 shipped."
    assert products_tool.calls == [
        {
            "query": "products",
            "min_price": None,
            "max_price": None,
        }
    ]
    assert order_status_tool.calls == [{"order_id": 12}]


@pytest.mark.anyio
async def test_langgraph_limits_tool_calls_per_batch_before_execution():
    product_tool = FakeTool("search_products", SearchProductsInput)
    batch_size = LangGraphAIService.MAX_TOOL_CALLS_PER_BATCH + 1
    response = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "search_products",
                "args": {"query": f"query-{index}"},
                "id": f"product-{index}",
                "type": "tool_call",
            }
            for index in range(batch_size)
        ],
    )
    service = LangGraphAIService(
        llm=FakeLLM([response]),
        search_products_tool=product_tool,
        search_knowledge_tool=FakeTool("search_knowledge", SearchKnowledgeInput),
        get_order_status_tool=FakeTool("get_order_status", GetOrderStatusInput),
        cancel_order_tool=FakeTool("cancel_order", CancelOrderInput),
        checkpointer=InMemorySaver(),
    )

    with pytest.raises(
        ValueError,
        match="Maximum number of tool calls per batch exceeded \\(5\\)",
    ):
        await service.chat("Search repeatedly", "langgraph-tool-batch-limit")

    assert product_tool.calls == []


@pytest.mark.anyio
async def test_langgraph_limits_total_tool_calls_per_request():
    product_tool = FakeTool("search_products", SearchProductsInput)
    batch_size = LangGraphAIService.MAX_TOOL_CALLS_PER_BATCH
    responses = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "search_products",
                    "args": {"query": f"query-{batch}-{index}"},
                    "id": f"product-{batch}-{index}",
                    "type": "tool_call",
                }
                for index in range(batch_size)
            ],
        )
        for batch in range(3)
    ]
    service = LangGraphAIService(
        llm=FakeLLM(responses),
        search_products_tool=product_tool,
        search_knowledge_tool=FakeTool("search_knowledge", SearchKnowledgeInput),
        get_order_status_tool=FakeTool("get_order_status", GetOrderStatusInput),
        cancel_order_tool=FakeTool("cancel_order", CancelOrderInput),
        checkpointer=InMemorySaver(),
    )

    with pytest.raises(
        ValueError,
        match="Maximum number of tool calls per request exceeded \\(10\\)",
    ):
        await service.chat("Search repeatedly", "langgraph-tool-request-limit")

    assert len(product_tool.calls) == LangGraphAIService.MAX_TOOL_CALLS_PER_REQUEST


@pytest.mark.anyio
async def test_langgraph_rejects_multiple_tool_calls_with_write_action():
    cancel_tool = FakeTool("cancel_order", CancelOrderInput)
    service = build_service(
        FakeLLM(
            [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "search_products",
                            "args": {"query": "products"},
                            "id": "products-before-cancel",
                            "type": "tool_call",
                        },
                        {
                            "name": "cancel_order",
                            "args": {"order_id": 42},
                            "id": "cancel-mixed-1",
                            "type": "tool_call",
                        },
                    ],
                )
            ]
        ),
        cancel_tool,
    )

    with pytest.raises(
        ValueError,
        match="Multiple tool calls containing write actions are not supported",
    ):
        await service.chat(
            message="Show products and cancel order 42",
            conversation_id="mixed-read-write-tools",
        )

    assert cancel_tool.calls == []


@pytest.mark.anyio
async def test_langgraph_resumes_confirmed_action():
    cancel_tool = FakeTool(
        "cancel_order",
        CancelOrderInput,
        result={"success": True},
    )
    service = build_service(
        FakeLLM(
            [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "cancel_order",
                            "args": {"order_id": 42},
                            "id": "cancel-1",
                            "type": "tool_call",
                        }
                    ],
                ),
                AIMessage(content="The order was cancelled."),
            ]
        ),
        cancel_tool,
    )

    pending = await service.chat(
        message="Cancel order 42",
        conversation_id="confirmed-action",
    )
    result = await service.chat(
        message="",
        conversation_id="confirmed-action",
        confirm_action=True,
    )

    assert pending.requires_confirmation is True
    assert pending.conversation_id == "confirmed-action"
    assert result.answer == "The order was cancelled."
    assert cancel_tool.calls == [{"order_id": 42}]


@pytest.mark.anyio
async def test_langgraph_rejects_action_without_executing_tool():
    cancel_tool = FakeTool("cancel_order", CancelOrderInput)
    service = build_service(
        FakeLLM(
            [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "cancel_order",
                            "args": {"order_id": 42},
                            "id": "cancel-2",
                            "type": "tool_call",
                        }
                    ],
                )
            ]
        ),
        cancel_tool,
    )

    await service.chat(
        message="Cancel order 42",
        conversation_id="rejected-action",
    )
    result = await service.chat(
        message="",
        conversation_id="rejected-action",
        confirm_action=False,
    )

    assert result.answer == "The action was not completed."
    assert result.requires_confirmation is False
    assert cancel_tool.calls == []


@pytest.mark.anyio
async def test_langgraph_resumes_action_from_persistent_postgres_checkpoint(
    test_database_url,
):
    cancel_tool = FakeTool(
        "cancel_order",
        CancelOrderInput,
        result={"success": True},
    )

    conversation_id = f"postgres-persistence-{uuid.uuid4()}"

    # First application/service lifetime.
    async with AsyncPostgresSaver.from_conn_string(
        test_database_url,
    ) as checkpointer:
        await checkpointer.setup()

        service = LangGraphAIService(
            llm=FakeLLM(
                [
                    AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "cancel_order",
                                "args": {"order_id": 42},
                                "id": "persistent-cancel-1",
                                "type": "tool_call",
                            }
                        ],
                    )
                ]
            ),
            search_products_tool=FakeTool(
                "search_products",
                SearchProductsInput,
            ),
            search_knowledge_tool=FakeTool(
                "search_knowledge",
                SearchKnowledgeInput,
            ),
            get_order_status_tool=FakeTool(
                "get_order_status",
                GetOrderStatusInput,
            ),
            cancel_order_tool=cancel_tool,
            checkpointer=checkpointer,
        )

        pending = await service.chat(
            message="Cancel order 42",
            conversation_id=conversation_id,
        )

        assert pending.requires_confirmation is True

    # The first checkpointer is now closed.
    # Create a completely new checkpointer and service.
    async with AsyncPostgresSaver.from_conn_string(
        test_database_url,
    ) as checkpointer:
        service = LangGraphAIService(
            llm=FakeLLM(
                [
                    AIMessage(
                        content="The order was cancelled.",
                    )
                ]
            ),
            search_products_tool=FakeTool(
                "search_products",
                SearchProductsInput,
            ),
            search_knowledge_tool=FakeTool(
                "search_knowledge",
                SearchKnowledgeInput,
            ),
            get_order_status_tool=FakeTool(
                "get_order_status",
                GetOrderStatusInput,
            ),
            cancel_order_tool=cancel_tool,
            checkpointer=checkpointer,
        )

        result = await service.chat(
            message="",
            conversation_id=conversation_id,
            confirm_action=True,
        )

    assert result.answer == "The order was cancelled."
    assert result.requires_confirmation is False
    assert cancel_tool.calls == [{"order_id": 42}]
