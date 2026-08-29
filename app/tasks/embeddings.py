from app.core.database import SessionLocal
from app.core.dependencies.ai import get_embedding_client
from app.repositories.product import ProductRepository
from app.services.embeddings import build_product_text
from app.tasks.celery import celery_app


@celery_app.task(
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_backoff_max=300,
    retry_jitter=False,
    max_retries=3,
)
def generate_product_embedding_task(product_id: int) -> None:
    db = SessionLocal()

    try:
        product = ProductRepository(db).get(product_id)

        if product is None:
            return

        product.embedding = get_embedding_client().embed(
            build_product_text(product)
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
