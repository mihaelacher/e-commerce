from sqlalchemy.orm import Session

from app.core.database import transaction
from app.exceptions import ProductNotFoundError
from app.models.product import ProductModel
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate
from app.tasks.embeddings import generate_product_embedding_task


def get_product(
    db: Session,
    product_id: int,
) -> ProductModel:
    repository = ProductRepository(db)

    product = repository.get(product_id)

    if product is None:
        raise ProductNotFoundError(product_id)

    return product


def list_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> list[ProductModel]:
    repository = ProductRepository(db)

    return repository.list_all(skip=skip, limit=limit)


def create_product(
    db: Session,
    product: ProductCreate,
) -> ProductModel:
    repository = ProductRepository(db)

    with transaction(db):
        db_product = repository.create(product.model_dump())

    generate_product_embedding_task.delay(db_product.id)
    return db_product


def update_product(
    db: Session,
    product_id: int,
    product: ProductUpdate,
) -> ProductModel:
    repository = ProductRepository(db)

    with transaction(db):
        db_product = repository.get(product_id)

        if db_product is None:
            raise ProductNotFoundError(product_id)

        updated_product = repository.update(
            db_product,
            product.model_dump(exclude_unset=True),
        )

        searchable_fields_changed = any(
            field in product.model_fields_set
            for field in ("name", "description")
        )
        if searchable_fields_changed:
            updated_product.embedding = None

    if searchable_fields_changed:
        generate_product_embedding_task.delay(updated_product.id)

    return updated_product


def delete_product(
    db: Session,
    product_id: int,
) -> None:
    repository = ProductRepository(db)

    with transaction(db):
        db_product = repository.get(product_id)

        if db_product is None:
            raise ProductNotFoundError(product_id)

        repository.delete(db_product)
