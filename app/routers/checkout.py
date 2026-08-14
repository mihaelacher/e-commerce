from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.checkout import CheckoutItem, OrderCreate, OrderResponse
from app.services import checkout as checkout_service

router = APIRouter(
    prefix="/checkout",
    tags=["Checkout"],
)


@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
):
    return checkout_service.get_order_with_items(db, order_id=order_id)


@router.post(
    "/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
):
    return checkout_service.create_order(
        db,
        email=order_data.email,
    )


@router.post(
    "/orders/{order_id}/items",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_to_cart(
    order_id: int,
    checkout_item: CheckoutItem,
    db: Session = Depends(get_db),
):
    return checkout_service.add_order_item(
        db,
        order_id=order_id,
        product_id=checkout_item.product_id,
        quantity=checkout_item.quantity,
    )


@router.delete(
    "/orders/{order_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_order_item(
    order_id: int,
    item_id: int,
    db: Session = Depends(get_db),
):
    checkout_service.remove_order_item(
        db,
        order_id=order_id,
        item_id=item_id,
    )


@router.patch(
    "/orders/{order_id}/items/{item_id}/decrease",
    response_model=OrderResponse,
)
def decrease_order_item(
    order_id: int,
    item_id: int,
    db: Session = Depends(get_db),
):
    return checkout_service.decrease_order_item(
        db,
        order_id=order_id,
        item_id=item_id,
    )


@router.post(
    "/orders/{order_id}/checkout",
    response_model=OrderResponse,
)
def checkout(
    order_id: int,
    db: Session = Depends(get_db),
):
    return checkout_service.checkout(
        db,
        order_id=order_id,
    )
