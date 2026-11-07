EVAL_CASES = [
    {
        "message": "Show me laptops",
        "expected_tool_calls": [
            {
                "name": "search_products",
                "arguments": {},
                "expected_query_terms": ["laptop", "laptops"],
            }
        ],
    },
    {
        "message": "Find a laptop under 800",
        "expected_tool_calls": [
            {
                "name": "search_products",
                "arguments": {"query": "laptop", "max_price": 800},
            }
        ],
    },
    {
        "message": "Find headphones between 50 and 150",
        "expected_tool_calls": [
            {
                "name": "search_products",
                "arguments": {
                    "query": "headphones",
                    "min_price": 50,
                    "max_price": 150,
                },
            }
        ],
    },
    {
        "message": "What is the status of order 12?",
        "expected_tool_calls": [
            {
                "name": "get_order_status",
                "arguments": {"order_id": 12},
            }
        ],
    },
    {
        "message": "Cancel order 42",
        "expected_tool_calls": [
            {
                "name": "cancel_order",
                "arguments": {"order_id": 42},
            }
        ],
    },
    {
        "message": "Please cancel my order number 9876",
        "expected_tool_calls": [
            {
                "name": "cancel_order",
                "arguments": {"order_id": 9876},
            }
        ],
    },
    {
        "message": "Can I cancel order 12?",
        "expected_tool_calls": [
            {
                "name": "search_knowledge",
                "arguments": {},
                "expected_query_terms": ["cancel", "cancellation", "policy"],
            },
            {
                "name": "get_order_status",
                "arguments": {"order_id": 12},
            },
        ],
    },
    {
        "message": "Don't cancel order 12. Just tell me its status.",
        "expected_tool_calls": [
            {
                "name": "get_order_status",
                "arguments": {"order_id": 12},
            }
        ],
    },
    {
        "message": "Tell me a joke",
        "expected_tool_calls": [],
    },
    {
        "message": "I need something cheap for listening to music",
        "expected_tool_calls": [
            {
                "name": "search_products",
                "arguments": {},
                "expected_query_terms": [
                    "headphones",
                    "earphones",
                    "earbuds",
                    "music",
                ],
            }
        ],
    },
    {
        "message": "Check order number 99999",
        "expected_tool_calls": [
            {
                "name": "get_order_status",
                "arguments": {"order_id": 99999},
            }
        ],
    },
    {
        "message": "Find me a laptop under 1",
        "expected_tool_calls": [
            {
                "name": "search_products",
                "arguments": {"query": "laptop", "max_price": 1},
            }
        ],
    },
    {
        "message": "What products do you have and what is the status of order 12?",
        "expected_tool_calls": [
            {
                "name": "search_products",
                "arguments": {},
                "expected_query_terms": [
                    "product",
                    "catalog",
                ],
            },
            {
                "name": "get_order_status",
                "arguments": {
                    "order_id": 12,
                },
            },
        ],
    },
    {
        "message": "How many days do I have to return a product?",
        "expected_tool_calls": [
            {
                "name": "search_knowledge",
                "arguments": {},
                "expected_query_terms": ["return", "returns", "return policy"],
            }
        ],
    },
    {
        "message": "Can I return an opened product?",
        "expected_tool_calls": [
            {
                "name": "search_knowledge",
                "arguments": {},
                "expected_query_terms": ["opened", "return"],
            }
        ],
    },
    {
        "message": "How long does standard shipping take?",
        "expected_tool_calls": [
            {
                "name": "search_knowledge",
                "arguments": {},
                "expected_query_terms": ["shipping", "delivery"],
            }
        ],
    },
    {
        "message": "Does the warranty cover accidental damage?",
        "expected_tool_calls": [
            {
                "name": "search_knowledge",
                "arguments": {},
                "expected_query_terms": ["warranty", "accidental damage"],
            }
        ],
    },
]


RETRIEVAL_CASES = [
    {
        "query": "wireless headphones",
        "expected_products": [
            "Wireless Headphones",
        ],
        "candidate_products": [
            "Wireless Headphones",
            "Gaming Headset",
            "Bluetooth Earbuds",
            "Studio Headphones",
            "Wireless Mouse",
        ],
    },
    {
        "query": "laptop stand",
        "expected_products": [
            "Laptop Stand",
        ],
        "candidate_products": [
            "Laptop Stand",
            "Laptop Backpack",
            "Desk Mat",
            "USB-C Hub",
            "Mechanical Keyboard",
        ],
    },
    {
        "query": "industrial refrigerator",
        "expected_products": [],
        "candidate_products": [
            "Wireless Mouse",
            "Desk Lamp",
            "USB-C Cable",
            "Laptop Backpack",
            "Wireless Headphones",
        ],
    },
]
