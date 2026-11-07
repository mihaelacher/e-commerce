from pydantic import BaseModel, Field


class SearchProductsInput(BaseModel):
    query: str
    min_price: float | None = Field(
        default=None,
        ge=0,
    )
    max_price: float | None = Field(
        default=None,
        ge=0,
    )


class GetOrderStatusInput(BaseModel):
    order_id: int = Field(gt=0)


class CancelOrderInput(BaseModel):
    order_id: int = Field(gt=0)


class SearchKnowledgeInput(BaseModel):
    query: str = Field(min_length=1)
