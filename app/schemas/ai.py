from decimal import Decimal

from pydantic import BaseModel, Field


class AIChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class AIChatResponse(BaseModel):
    answer: str


class ProductSearchQuery(BaseModel):
    search_query: str
    min_price: Decimal | None = None
    max_price: Decimal | None = None    