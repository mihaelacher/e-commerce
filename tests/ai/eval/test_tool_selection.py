import json

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.clients.openai.langchain_client import LangChainClient
from app.ai.prompts.ecommerce_agent import ECOMMERCE_AGENT_SYSTEM_PROMPT
from app.ai.tools.cancel_order import CancelOrderTool
from app.ai.tools.get_order_status import GetOrderStatusTool
from app.ai.tools.search_knowledge import SearchKnowledgeTool
from app.ai.tools.search_products import SearchProductsTool
from tests.ai.eval.cases import EVAL_CASES
from tests.ai.eval.metrics import tool_selection_metrics


@pytest.mark.eval
@pytest.mark.anyio
async def test_tool_selection_eval():
    llm = LangChainClient().get_client()

    tools = [
        {
            "type": "function",
            "function": tool.definition,
        }
        for tool in (
            SearchProductsTool,
            GetOrderStatusTool,
            CancelOrderTool,
            SearchKnowledgeTool,
        )
    ]
    llm_with_tools = llm.bind_tools(tools)

    results = []
    for case in EVAL_CASES:
        response = await llm_with_tools.ainvoke(
            [
                SystemMessage(content=ECOMMERCE_AGENT_SYSTEM_PROMPT),
                HumanMessage(content=case["message"]),
            ]
        )
        tool_call = response.tool_calls[0] if response.tool_calls else None

        results.append(
            {
                **case,
                "actual_tool": tool_call["name"] if tool_call else None,
                "actual_arguments": tool_call["args"] if tool_call else None,
            }
        )

    metrics = tool_selection_metrics(results)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))

    assert metrics["tool_selection_accuracy"] >= 0.9
    assert metrics["argument_accuracy"] >= 0.9
