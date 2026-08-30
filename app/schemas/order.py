from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrderBase(BaseModel):
    status: str = Field(
        min_length=1,
        max_length=100,
    )

    total: Decimal = Field(
        ge=0,
        decimal_places=2,
    )

    tax: Decimal = Field(
        ge=0,
        decimal_places=2,
    )

    shipping: Decimal = Field(
        ge=0,
        decimal_places=2,
    )

    discount: Decimal = Field(
        ge=0,
        decimal_places=2,
    )

    email: str = Field(
        min_length=1,
        max_length=100,
    )


class OrderResponse(OrderBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    created_at: datetime
    updated_at: datetime | None = None