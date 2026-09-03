from decimal import Decimal

from pydantic import BaseModel, Field


class AIChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None
    confirm_action: bool | None = None


class AIChatResponse(BaseModel):
    answer: str
    conversation_id: str


class ProductSearchQuery(BaseModel):
    search_query: str
    min_price: Decimal | None = None
    max_price: Decimal | None = None
