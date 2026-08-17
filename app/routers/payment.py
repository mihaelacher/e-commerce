from fastapi import APIRouter, Header, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.payment import PaymentResponse
from app.services.payment import create_payment


router = APIRouter(
    prefix="/payments",
    tags=["payments"],
)


@router.post(
    "/orders/{order_id}",
    response_model=PaymentResponse,
)
def pay_order(
    order_id: int,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
) -> PaymentResponse:
    return create_payment(
        db=db,
        order_id=order_id,
        idempotency_key=idempotency_key,
    )