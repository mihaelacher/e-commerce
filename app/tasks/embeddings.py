from app.core.database import SessionLocal
from app.core.dependencies.ai import get_embedding_client
from app.core.logging import capture_exception, get_logger
from app.repositories.product.sync import ProductRepository
from app.services.embeddings import build_product_text
from app.tasks.celery import celery_app

logger = get_logger(__name__)


@celery_app.task(
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_backoff_max=300,
    retry_jitter=False,
    max_retries=3,
)
def generate_product_embedding_task(product_id: int) -> None:
    db = SessionLocal()

    logger.info("embedding_task_started", extra={"product_id": product_id})

    try:
        product = ProductRepository(db).get(product_id)

        if product is None:
            logger.warning("embedding_task_product_missing", extra={"product_id": product_id})
            return

        text = build_product_text(product)

        logger.info(
            "embedding_generation_started",
            extra={
                "product_id": product_id,
                "text_length": len(text),
            },
        )

        embedding = get_embedding_client().embed(text)
        product.embedding = embedding
        db.commit()

        logger.info(
            "embedding_task_completed",
            extra={
                "product_id": product_id,
                "embedding_size": len(embedding),
            },
        )
        
    except Exception as exc:
        db.rollback()
        logger.exception("embedding_task_failed", extra={"product_id": product_id})
        capture_exception(exc, product_id=product_id)
        raise
    finally:
        db.close()
