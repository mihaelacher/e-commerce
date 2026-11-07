from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
    )
    price: Decimal = Field(
        gt=0,
        decimal_places=2,
    )
    stock: int = Field(
        default=0,
        ge=0,
    )


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
    )
    price: Decimal | None = Field(
        default=None,
        gt=0,
        decimal_places=2,
    )
    stock: int | None = Field(
        default=None,
        ge=0,
    )


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime | None = None
