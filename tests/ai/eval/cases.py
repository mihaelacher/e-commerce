EVAL_CASES = [
    {
        "message": "Show me laptops",
        "expected_tool": "search_products",
        "expected_arguments": {},
        "expected_query_terms": [
            "laptop",
            "laptops",
        ],
    },
    {
        "message": "Find a laptop under 800",
        "expected_tool": "search_products",
        "expected_arguments": {
            "query": "laptop",
            "max_price": 800,
        },
    },
    {
        "message": "Find headphones between 50 and 150",
        "expected_tool": "search_products",
        "expected_arguments": {
            "query": "headphones",
            "min_price": 50,
            "max_price": 150,
        },
    },
    {
        "message": "What is the status of order 12?",
        "expected_tool": "get_order_status",
        "expected_arguments": {
            "order_id": 12,
        },
    },
    {
        "message": "Tell me a joke",
        "expected_tool": None,
        "expected_arguments": None,
    },
   {
        "message": "I need something cheap for listening to music",
        "expected_tool": "search_products",
        "expected_arguments": {},
        "expected_query_terms": [
            "headphones",
            "earphones",
            "earbuds",
            "music",
        ],
    },
    {
        "message": "Check order number 99999",
        "expected_tool": "get_order_status",
        "expected_arguments": {
            "order_id": 99999,
        },
    },
    {
        "message": "Find me a laptop under 1",
        "expected_tool": "search_products",
        "expected_arguments": {
            "query": "laptop",
            "max_price": 1,
        },
    },
    {
        "message": "What products do you have and what is the status of order 12?",
        "expected_tool": "search_products",
        "expected_arguments": {
            "query": "products",
        },
    },
]