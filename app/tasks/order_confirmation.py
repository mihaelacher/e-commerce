from decimal import Decimal

from app.integrations import n8n_client
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


@celery_app.task
def notify_order_created_task(
    order_id: int,
    total: str,
) -> None:
    n8n_client.order_created(
        order_id=order_id,
        total=total,
    )