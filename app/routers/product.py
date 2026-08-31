from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.product import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from app.services import product as product_service

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product: ProductCreate,
    db: Annotated[Session, Depends(get_db)],
):
    return product_service.create_product(
        db=db,
        product=product,
    )


@router.get(
    "/",
    response_model=list[ProductResponse],
)
def list_products(
    skip: Annotated[int, Query(ge=0, description="Number of products to skip")] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Maximum number of products to return"),
    ] = 100,
    db: Annotated[Session, Depends(get_db)] = None,
):
    return product_service.list_products(
        db,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    return product_service.get_product(
        db,
        product_id,
    )


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
)
def update_product(
    product_id: int,
    product: ProductUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    return product_service.update_product(
        db,
        product_id,
        product,
    )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    product_service.delete_product(
        db,
        product_id,
    )
