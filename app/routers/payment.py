from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_payment_provider
from app.schemas.payment import PaymentResponse
from app.services.payment import create_payment, handle_payment_webhook
from app.providers.payment.base import PaymentGateway


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
    provider: PaymentGateway = Depends(get_payment_provider),
) -> PaymentResponse:
    return create_payment(
        db=db,
        order_id=order_id,
        idempotency_key=idempotency_key,
        provider=provider,
    )

@router.post("/webhook")
@router.post("/webhook")
def payment_webhook(
    payload: dict,
    signature: str = Header(..., alias="X-Webhook-Signature"),
    db: Session = Depends(get_db),
    provider: PaymentGateway = Depends(get_payment_provider),
) -> PaymentResponse:

    if not provider.verify_webhook(payload, signature):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature",
        )

    return handle_payment_webhook(
        db=db,
        payload=payload,
        provider=provider,
    )