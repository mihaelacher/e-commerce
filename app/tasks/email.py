from decimal import Decimal

from app.services.email import send_order_confirmation
from app.tasks.celery import celery_app


@celery_app.task
def send_order_confirmation_task(
    recipient: str,
    order_id: int,
    total: str,
) -> None:
    send_order_confirmation(
        recipient=recipient,
        order_id=order_id,
        total=Decimal(total),
    )
