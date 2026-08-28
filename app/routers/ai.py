from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.clients.embedding_base import EmbeddingClient
from app.ai.clients.llm_base import LLMClient
from app.ai.clients.product_query_parser import ProductQueryParser
from app.core.database import get_db
from app.core.dependencies import get_ai_client, get_embedding_client, get_product_query_parser
from app.repositories.product import ProductRepository
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.services.ai import AIService


router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


@router.post("/chat", response_model=AIChatResponse)
def chat(
    payload: AIChatRequest,
    db: Session = Depends(get_db),
    ai_client: LLMClient = Depends(get_ai_client),
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
    query_parser: ProductQueryParser = Depends(get_product_query_parser),
) -> AIChatResponse:
    repository = ProductRepository(db)

    service = AIService(
        ai_client=ai_client,
        embedding_client=embedding_client,
        product_repository=repository,
        query_parser=query_parser,
    )

    return AIChatResponse(
        answer=service.chat(payload.message)
    )