import pytest

from tests.ai.eval.metrics import retrieval_metrics, tool_selection_metrics


def test_tool_selection_metrics_score_tools_arguments_and_queries():
    results = [
        {
            "message": "Find headphones under 100",
            "expected_tool_calls": [
                {
                    "name": "search_products",
                    "arguments": {"max_price": 100},
                    "expected_query_terms": ["headphones"],
                }
            ],
            "actual_tool_calls": [
                {
                    "name": "search_products",
                    "arguments": {"query": "headphones", "max_price": 100},
                }
            ],
        },
        {
            "message": "Find a laptop",
            "expected_tool_calls": [
                {
                    "name": "search_products",
                    "arguments": {},
                    "expected_query_terms": ["laptop"],
                }
            ],
            "actual_tool_calls": [
                {
                    "name": "search_products",
                    "arguments": {"query": "laptop"},
                }
            ],
        },
        {
            "message": "Tell me a joke",
            "expected_tool_calls": [],
            "actual_tool_calls": [],
        },
    ]

    metrics = tool_selection_metrics(results)

    assert metrics["cases"] == 3
    assert metrics["tool_selection_accuracy"] == 1.0
    assert metrics["argument_accuracy"] == 1.0
    assert metrics["case_accuracy"] == 1.0
    assert metrics["failures"] == []


def test_tool_selection_metrics_report_wrong_arguments():
    metrics = tool_selection_metrics(
        [
            {
                "message": "Find headphones under 100",
                "expected_tool_calls": [
                    {
                        "name": "search_products",
                        "arguments": {"max_price": 100},
                    }
                ],
                "actual_tool_calls": [
                    {
                        "name": "search_products",
                        "arguments": {"max_price": 200},
                    }
                ],
            }
        ]
    )

    assert metrics["tool_selection_accuracy"] == 1.0
    assert metrics["argument_accuracy"] == 0.0
    assert metrics["case_accuracy"] == 0.0
    assert len(metrics["failures"]) == 1


def test_tool_selection_metrics_score_multiple_tools_and_arguments():
    metrics = tool_selection_metrics(
        [
            {
                "message": "Show products and check order status",
                "expected_tool_calls": [
                    {
                        "name": "search_products",
                        "arguments": {"query": "products"},
                    },
                    {
                        "name": "get_order_status",
                        "arguments": {"order_id": 12},
                    },
                ],
                "actual_tool_calls": [
                    {
                        "name": "get_order_status",
                        "arguments": {"order_id": 12},
                    },
                    {
                        "name": "search_products",
                        "arguments": {"query": "products"},
                    },
                ],
            }
        ]
    )

    assert metrics["tool_selection_accuracy"] == 1.0
    assert metrics["argument_accuracy"] == 1.0
    assert metrics["case_accuracy"] == 1.0
    assert metrics["failures"] == []


def test_tool_selection_metrics_fail_when_expected_tool_is_missing():
    metrics = tool_selection_metrics(
        [
            {
                "message": "Show products and check order status",
                "expected_tool_calls": [
                    {
                        "name": "search_products",
                        "arguments": {"query": "products"},
                    },
                    {
                        "name": "get_order_status",
                        "arguments": {"order_id": 12},
                    },
                ],
                "actual_tool_calls": [
                    {
                        "name": "get_order_status",
                        "arguments": {"order_id": 12},
                    }
                ],
            }
        ]
    )

    assert metrics["tool_selection_accuracy"] == 0.0
    assert metrics["argument_accuracy"] == 0.0
    assert metrics["case_accuracy"] == 0.0
    assert metrics["failures"][0]["actual_tool_calls"] == [
        {
            "name": "get_order_status",
            "arguments": {"order_id": 12},
        }
    ]


def test_retrieval_metrics_calculate_recall_mrr_and_no_answer_accuracy():
    metrics = retrieval_metrics(
        [
            {
                "query": "wireless audio",
                "expected": ["Wireless Headphones", "Bluetooth Earbuds"],
                "retrieved": [
                    "Gaming Headset",
                    "Wireless Headphones",
                ],
            },
            {
                "query": "industrial refrigerator",
                "expected": [],
                "retrieved": [],
            },
        ],
        k=5,
    )

    assert metrics["cases"] == 2
    assert metrics["precision_at_k"] == 0.2
    assert metrics["recall_at_k"] == 0.5
    assert metrics["mrr_at_k"] == 0.5
    assert metrics["no_answer_accuracy"] == 1.0
    assert metrics["failures"] == [
        {
            "query": "wireless audio",
            "expected": ["Bluetooth Earbuds", "Wireless Headphones"],
            "retrieved": ["Gaming Headset", "Wireless Headphones"],
        }
    ]


def test_retrieval_precision_uses_k_as_denominator_when_fewer_results_returned():
    metrics = retrieval_metrics(
        [
            {
                "query": "specific item",
                "expected": ["Expected Product"],
                "retrieved": ["Expected Product"],
            }
        ],
        k=5,
    )

    assert metrics["precision_at_k"] == 0.2


@pytest.mark.parametrize(
    ("results", "k"),
    [
        ([], 5),
        ([{"query": "anything", "expected": [], "retrieved": []}], 0),
    ],
)
def test_retrieval_metrics_reject_invalid_inputs(results, k):
    with pytest.raises(ValueError):
        retrieval_metrics(results, k=k)


def test_tool_selection_metrics_reject_empty_results():
    with pytest.raises(ValueError):
        tool_selection_metrics([])
