from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.analytics.sales import best_selling_products, daily_sales
from app.repositories.analytics import AnalyticsRepository

REPORTING_TIMEZONE = ZoneInfo("Europe/Sofia")


def _date_range(
    from_date: date | None,
    to_date: date | None,
) -> tuple[datetime | None, datetime | None]:
    start = (
        datetime.combine(from_date, time.min, tzinfo=REPORTING_TIMEZONE)
        if from_date
        else None
    )
    end = (
        datetime.combine(
            to_date + timedelta(days=1),
            time.min,
            tzinfo=REPORTING_TIMEZONE,
        )
        if to_date
        else None
    )

    return start, end


def get_best_selling_products(
    db: Session,
    from_date: date | None = None,
    to_date: date | None = None,
    limit: int = 10,
) -> list[dict]:
    start, end = _date_range(from_date, to_date)

    repository = AnalyticsRepository(db)
    data = repository.get_sales_data(start, end)

    return best_selling_products(data, limit)


def get_daily_sales(
    db: Session,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[dict]:
    now = datetime.now(REPORTING_TIMEZONE)

    if from_date is None and to_date is None:
        from_date = to_date = now.date()

    start, end = _date_range(from_date, to_date)

    repository = AnalyticsRepository(db)
    data = repository.get_sales_data(from_date=start, to_date=end)

    return daily_sales(data)