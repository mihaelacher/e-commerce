from datetime import date

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
      from_date: date | None = Query(
        None,
        alias="from",
    ),
    to_date: date | None = Query(
        None,
        alias="to",
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
):
    return analytics_service.get_best_selling_products(db, from_date, to_date, limit)


@router.get("/sales/daily")
def get_daily_sales(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
):
    return analytics_service.get_daily_sales(db, from_date, to_date)