from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "ecommerce",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=[
        "app.tasks.order_confirmation",
        "app.tasks.embeddings",
        "app.tasks.payment",
        "app.tasks.refund_payment",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
