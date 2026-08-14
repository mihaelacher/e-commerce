from sqlalchemy.orm import Session

from app.core.database import transaction
from app.exceptions import ProductNotFoundError
from app.models.product import ProductModel
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate


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
        return repository.create(product.model_dump())


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

        return repository.update(
            db_product,
            product.model_dump(exclude_unset=True),
        )


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
