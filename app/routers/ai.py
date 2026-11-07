import json
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.core.dependencies.ai import get_ai_service, get_langgraph_ai_service
from app.core.logging import get_logger
from app.core.rate_limit import enforce_ai_rate_limit
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.services.ai.ai import AIService
from app.services.ai.langgraph_ai import LangGraphAIService

router = APIRouter(
    prefix="/ai",
    tags=["Chat"],
)

logger = get_logger(__name__)

@router.post("/v1/chat", response_model=AIChatResponse)
async def chat(
    request: AIChatRequest,
    ai_service: Annotated[AIService, Depends(get_ai_service)],
    _: Annotated[None, Depends(enforce_ai_rate_limit)],
) -> AIChatResponse:
    conversation_id = request.conversation_id or str(uuid4())

    message = await ai_service.chat(
        message=request.message,
        conversation_id=conversation_id,
        confirm_action=request.confirm_action,
    )

    return AIChatResponse(
        answer=message,
        conversation_id=conversation_id,
    )


@router.post("/v2/chat", response_model=AIChatResponse)
async def chat_v2(
    request: AIChatRequest,
    service: Annotated[
        LangGraphAIService,
        Depends(get_langgraph_ai_service),
    ],
    _: Annotated[None, Depends(enforce_ai_rate_limit)],
) -> AIChatResponse:
    conversation_id = request.conversation_id or str(uuid4())

    return await service.chat(
        request.message,
        conversation_id=conversation_id,
        confirm_action=request.confirm_action,
    )


@router.post("/v2/chat/stream")
async def chat_v2_stream(
    request: AIChatRequest,
    http_request: Request,
    service: Annotated[
        LangGraphAIService,
        Depends(get_langgraph_ai_service),
    ],
    _: Annotated[None, Depends(enforce_ai_rate_limit)],
):
    conversation_id = request.conversation_id or str(uuid4())

    async def event_stream():
        try:
            async for event in service.stream_chat(
                request.message,
                conversation_id=conversation_id,
                confirm_action=request.confirm_action,
            ):
                if await http_request.is_disconnected():
                    break

                event_name = event["event"]
                payload = json.dumps(
                    event["data"],
                    ensure_ascii=False,
                )

                yield f"event: {event_name}\ndata: {payload}\n\n"

        except Exception:
            logger.exception("ai_stream_failed")

            payload = json.dumps(
                {"message": "An error occurred while processing the request."},
                ensure_ascii=False,
            )

            yield f"event: error\ndata: {payload}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )