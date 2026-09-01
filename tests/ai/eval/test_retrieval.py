import pytest

from deepeval.metrics import ContextualRelevancyMetric
from deepeval.models import GeminiModel
from deepeval.test_case import LLMTestCase

from app.ai.clients.gemini.embedding import GeminiEmbeddingClient
from app.ai.tools.search_products import SearchProductsTool
from app.core.config import settings
from app.core.database import SessionLocal
from app.repositories.product import ProductRepository
from tests.ai.eval.cases import RETRIEVAL_CASES


# TODO: deeleval library added
# not tested yet, since daily rate exceeded for Gemini API, 
# need to wait for next day to test it
@pytest.mark.eval
@pytest.mark.parametrize("case", RETRIEVAL_CASES)
def test_product_retrieval(case):
    with SessionLocal() as db:
        tool = SearchProductsTool(
            embedding_client=GeminiEmbeddingClient(),
            product_repository=ProductRepository(db),
        )

        results = tool.execute(
            query=case["query"],
        )

    retrieval_context = [
        (
            f"Product: {product['name']}. "
            f"Description: {product['description']}. "
            f"Price: {product['price']}. "
            f"Stock: {product['stock']}."
        )
        for product in results
    ]

    judge = GeminiModel(
        model="gemini-3.6-flash",
        api_key=settings.gemini_api_key,
        temperature=0,
    )

    test_case = LLMTestCase(
        input=case["query"],
        actual_output="Product search results",
        retrieval_context=retrieval_context,
    )

    metric = ContextualRelevancyMetric(
        threshold=0.7,
        model=judge,
        include_reason=True,
    )

    metric.measure(test_case)

    print(f"Query: {case['query']}")
    print(f"Score: {metric.score}")
    print(f"Reason: {metric.reason}")

    assert metric.score >= 0.7