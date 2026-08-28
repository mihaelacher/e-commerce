from app.ai.clients.embedding_base import EmbeddingClient
from app.ai.clients.gemini_embedding import GeminiEmbeddingClient
from app.ai.clients.llm_base import LLMClient
from app.ai.clients.gemini_client import GeminiClient
from app.ai.clients.product_query_parser import ProductQueryParser
from app.providers.payment.mock import MockPaymentProvider
from app.providers.payment.base import PaymentGateway


def get_payment_provider() -> PaymentGateway:
    return MockPaymentProvider()


def get_ai_client() -> LLMClient:
    return GeminiClient()


def get_embedding_client() -> EmbeddingClient:
    return GeminiEmbeddingClient()


def get_product_query_parser() -> ProductQueryParser:
    return ProductQueryParser()