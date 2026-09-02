from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.services import analytics as analytics_service

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get("/sales/products")
def get_best_selling_products(
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    db: Annotated[Session, Depends(get_db)] = None,
):
    return analytics_service.get_best_selling_products(db, from_date, to_date, limit)


@router.get("/sales/daily")
def get_daily_sales(
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
    db: Annotated[Session, Depends(get_db)] = None,
):
    return analytics_service.get_daily_sales(db, from_date, to_date)
