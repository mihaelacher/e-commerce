from fastapi import APIRouter, Depends

from app.core.dependencies.ai import get_ai_service
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.services.ai import AIService

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


@router.post("/chat", response_model=AIChatResponse)
def chat(
    request: AIChatRequest,
    service: AIService = Depends(get_ai_service),
):
    answer = service.chat(request.message)

    return AIChatResponse(answer=answer)