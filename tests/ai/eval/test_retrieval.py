import json

import pytest

from app.ai.tools.search_products import SearchProductsTool
from app.core.dependencies.ai import get_embedding_client
from app.models.product import ProductModel
from app.repositories.product.async_product import (
    AsyncProductRepository as ProductRepository,
)
from app.services.embeddings import build_product_text
from scripts.seed.product_data import PRODUCTS
from tests.ai.eval.cases import RETRIEVAL_CASES
from tests.ai.eval.metrics import retrieval_metrics


@pytest.mark.eval
@pytest.mark.asyncio
async def test_product_retrieval_eval(async_db):
    embedding_client = get_embedding_client()
    products_by_name = {product["name"]: product for product in PRODUCTS}

    result_cases = []
    for case in RETRIEVAL_CASES:
        candidates = [products_by_name[name] for name in case["candidate_products"]]

        for candidate in candidates:
            product = ProductModel(
                name=candidate["name"],
                description=candidate["description"],
                price=candidate["price"],
                stock=candidate["stock"],
            )
            product.embedding = await embedding_client.embed_async(
                build_product_text(product)
            )
            async_db.add(product)

        await async_db.flush()

        tool = SearchProductsTool(
            embedding_client=embedding_client,
            product_repository=ProductRepository(async_db),
        )

        retrieved = await tool.execute(
            query=case["query"],
        )

        result_cases.append(
            {
                "query": case["query"],
                "expected": case["expected_products"],
                "retrieved": [product["name"] for product in retrieved],
            }
        )
        await async_db.rollback()

    metrics = retrieval_metrics(result_cases, k=5)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))

    assert metrics["precision_at_k"] >= 0.2
    assert metrics["recall_at_k"] >= 0.9
    assert metrics["mrr_at_k"] >= 0.9
    assert metrics["no_answer_accuracy"] == 1.0
