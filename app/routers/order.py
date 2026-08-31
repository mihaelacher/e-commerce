from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.schemas.checkout import OrderResponse
from app.services import order as order_service

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
):
    return order_service.get_order(
        db,
        order_id,
    )