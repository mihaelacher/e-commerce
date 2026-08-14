from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "ecommerce",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=["app.tasks.email"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
