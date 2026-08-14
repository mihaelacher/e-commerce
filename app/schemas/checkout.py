from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.enums.order import OrderStatus


class CheckoutItem(BaseModel):
    product_id: int
    quantity: int = Field(default=1, gt=0)


class CheckoutRequest(BaseModel):
    items: list[CheckoutItem] = Field(min_length=1)


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    total_price: Decimal


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: OrderStatus
    subtotal: Decimal
    total: Decimal
    tax: Decimal
    shipping: Decimal
    discount: Decimal
    email: EmailStr
    created_at: datetime
    updated_at: datetime

    items: list[OrderItemResponse]


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    email: EmailStr
