from datetime import UTC, date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.analytics.sales import daily_sales
from app.enums.order import OrderStatus
from app.models.order import OrderModel
from app.models.order_item import OrderItemModel
from app.models.product import ProductModel
from app.repositories.analytics import AnalyticsRepository
from app.services.analytics import get_best_selling_products

REPORTING_TIMEZONE = ZoneInfo("Europe/Sofia")


def add_sale(
    db,
    *,
    product: ProductModel,
    created_at: datetime,
    quantity: int,
) -> None:
    order = OrderModel(
        email="analytics@example.com",
        status=OrderStatus.PAID,
        created_at=created_at,
    )
    db.add(order)
    db.flush()

    db.add(
        OrderItemModel(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=product.price,
            total_price=product.price * quantity,
        )
    )


def test_product_sales_to_date_is_inclusive_and_aggregated(db):
    product = ProductModel(
        name="Analytics Keyboard",
        price=Decimal("10.00"),
        stock=10,
    )
    db.add(product)
    db.flush()

    add_sale(
        db,
        product=product,
        created_at=datetime(2026, 8, 21, 12, 0, 0, tzinfo=REPORTING_TIMEZONE),
        quantity=2,
    )
    add_sale(
        db,
        product=product,
        created_at=datetime(2026, 8, 21, 23, 59, 59, tzinfo=REPORTING_TIMEZONE),
        quantity=1,
    )
    add_sale(
        db,
        product=product,
        created_at=datetime(2026, 8, 22, 0, 0, 0, tzinfo=REPORTING_TIMEZONE),
        quantity=10,
    )
    db.commit()

    result = get_best_selling_products(
        db,
        from_date=date(2026, 8, 21),
        to_date=date(2026, 8, 21),
    )

    assert len(result) == 1
    assert result[0]["product_id"] == product.id
    assert result[0]["units_sold"] == 3
    assert result[0]["revenue"] == Decimal("30.00")


def test_daily_sales_is_aggregated_by_pandas(db):
    product = ProductModel(
        name="Daily Analytics Keyboard",
        price=Decimal("10.00"),
        stock=10,
    )
    db.add(product)
    db.flush()

    add_sale(
        db,
        product=product,
        created_at=datetime(2026, 8, 21, 12, 0, 0, tzinfo=UTC),
        quantity=2,
    )
    add_sale(
        db,
        product=product,
        created_at=datetime(2026, 8, 21, 13, 0, 0, tzinfo=UTC),
        quantity=1,
    )
    db.commit()

    rows = AnalyticsRepository(db).get_sales_data(
        datetime(2026, 8, 21, tzinfo=UTC),
        datetime(2026, 8, 22, tzinfo=UTC),
    )

    result = daily_sales(rows)

    assert len(result) == 1
    assert result[0]["orders"] == 2
    assert result[0]["units_sold"] == 3
    assert result[0]["revenue"] == Decimal("30.00")
