import pytest

from app.ai.clients.gemini.client import GeminiClient
from app.ai.tools.cancel_order import CancelOrderTool
from app.ai.tools.get_order_status import GetOrderStatusTool
from app.ai.tools.search_knowledge import SearchKnowledgeTool
from app.ai.tools.search_products import SearchProductsTool
from tests.ai.eval.cases import EVAL_CASES


def assert_query(
    actual_query: str,
    expected_terms: list[str],
) -> None:
    actual_query = actual_query.lower()

    assert any(term.lower() in actual_query for term in expected_terms)


def assert_arguments(
    actual: dict,
    expected: dict,
) -> None:
    for key, expected_value in expected.items():
        assert key in actual
        assert actual[key] == expected_value


@pytest.mark.eval
@pytest.mark.parametrize("case", EVAL_CASES)
@pytest.mark.anyio
async def test_tool_selection(case):
    client = GeminiClient()

    tools = [
        SearchProductsTool.definition,
        GetOrderStatusTool.definition,
        CancelOrderTool.definition,
        SearchKnowledgeTool.definition,
    ]

    response = await client.chat(
        message=case["message"],
        tools=tools,
    )

    expected_tool = case["expected_tool"]

    if expected_tool is None:
        assert response.tool_call is None
        return

    assert response.tool_call is not None
    assert response.tool_call.name == expected_tool

    assert_arguments(
        actual=response.tool_call.arguments,
        expected=case["expected_arguments"],
    )

    if "expected_query_terms" in case:
        assert_query(
            actual_query=response.tool_call.arguments["query"],
            expected_terms=case["expected_query_terms"],
        )
