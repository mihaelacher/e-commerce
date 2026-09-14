from langchain_core.tools import StructuredTool

from app.ai.tools.cancel_order import CancelOrderTool
from app.ai.tools.get_order_status import GetOrderStatusTool
from app.ai.tools.search_knowledge import SearchKnowledgeTool
from app.ai.tools.search_products import SearchProductsTool


def to_langchain_search_products_tool(
    tool: SearchProductsTool,
) -> StructuredTool:
    return StructuredTool.from_function(
        coroutine=tool.execute,
        name=tool.name,
        description=(
            "Search available products matching the customer's request."
        ),
        args_schema=tool.input_model,
    )


def to_langchain_search_knowledge_tool(
    tool: SearchKnowledgeTool,
) -> StructuredTool:
    return StructuredTool.from_function(
        coroutine=tool.execute,
        name=tool.name,
        description=(
            "Search store policies, FAQs, and product guides for information "
            "relevant to the user's question."
        ),
        args_schema=tool.input_model,
    )


def to_langchain_get_order_status_tool(
    tool: GetOrderStatusTool,
) -> StructuredTool:
    return StructuredTool.from_function(
        coroutine=tool.execute,
        name=tool.name,
        description=(
            "Get the current status of an order."
        ),
        args_schema=tool.input_model,
    )


def to_langchain_cancel_order_tool(
    tool: CancelOrderTool,
) -> StructuredTool:
    return StructuredTool.from_function(
        coroutine=tool.execute,
        name=tool.name,
        description=(
            "Cancel an existing customer order. "
            "Use this tool when the customer explicitly requests "
            "cancellation of an order."
        ),
        args_schema=tool.input_model,
    )