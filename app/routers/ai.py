from uuid import uuid4

from fastapi import APIRouter, Depends

from app.core.dependencies.ai import get_ai_service
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.services.ai import AIService

router = APIRouter(
    prefix="/ai",
    tags=["Chat"],
)


@router.post("/chat", response_model=AIChatResponse)
def chat(
    request: AIChatRequest,
    ai_service: AIService = Depends(get_ai_service),
) -> AIChatResponse:
    conversation_id = (
        request.conversation_id
        or str(uuid4())
    )

    message = ai_service.chat(
        message=request.message,
        conversation_id=conversation_id,
    )

    return AIChatResponse(
        answer=message,
        conversation_id=conversation_id,
    )