import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal, transaction
from app.enums.order import OrderStatus
from app.models.product import ProductModel
from app.repositories.order import OrderRepository
from app.repositories.order_item import OrderItemRepository
from scripts.seed.product_data import PRODUCTS


NUMBER_OF_ORDERS = 100
DAYS_OF_HISTORY = 30


def get_product_weights(
    products: list[ProductModel],
) -> list[int]:
    weights_by_name = {
        product["name"]: product["sales_weight"]
        for product in PRODUCTS
    }

    return [
        weights_by_name[product.name]
        for product in products
    ]


def choose_products(
    products: list[ProductModel],
    count: int,
) -> list[ProductModel]:
    available_products = products.copy()
    selected_products: list[ProductModel] = []

    while len(selected_products) < count:
        weights = get_product_weights(available_products)

        product = random.choices(
            available_products,
            weights=weights,
            k=1,
        )[0]

        selected_products.append(product)
        available_products.remove(product)

    return selected_products


def random_order_date() -> datetime:
    now = datetime.now(timezone.utc)

    days_ago = random.randint(0, DAYS_OF_HISTORY - 1)
    hours_ago = random.randint(0, 23)
    minutes_ago = random.randint(0, 59)

    return now - timedelta(
        days=days_ago,
        hours=hours_ago,
        minutes=minutes_ago,
    )


def random_order_status() -> OrderStatus:
    return random.choices(
        [
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED,
            OrderStatus.PAYMENT_PENDING,
            OrderStatus.PENDING,
        ],
        weights=[70, 10, 10, 10],
        k=1,
    )[0]


def calculate_order_totals(
    subtotal: Decimal,
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    tax = (subtotal * Decimal("0.20")).quantize(
        Decimal("0.01")
    )

    shipping = (
        Decimal("0.00")
        if subtotal >= Decimal("100.00")
        else Decimal("9.99")
    )

    discount = (
        (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
        if subtotal >= Decimal("200.00")
        else Decimal("0.00")
    )

    total = subtotal + tax + shipping - discount

    return tax, shipping, discount, total


def seed_orders(
    number_of_orders: int = NUMBER_OF_ORDERS,
) -> None:
    db = SessionLocal()

    try:
        order_repository = OrderRepository(db)
        order_item_repository = OrderItemRepository(db)

        products = db.scalars(
            select(ProductModel)
        ).all()

        if not products:
            raise RuntimeError(
                "No products found. Seed products first."
            )

        with transaction(db):
            for order_number in range(1, number_of_orders + 1):
                order = order_repository.create(
                    email=f"customer{order_number}@example.com",
                )

                order.created_at = random_order_date()

                product_count = random.randint(1, 4)

                selected_products = choose_products(
                    products=products,
                    count=product_count,
                )

                subtotal = Decimal("0.00")

                for product in selected_products:
                    quantity = random.randint(1, 5)

                    item = order_item_repository.create(
                        order=order,
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=product.price,
                    )

                    subtotal += item.total_price

                tax, shipping, discount, total = (
                    calculate_order_totals(subtotal)
                )

                order.subtotal = subtotal
                order.tax = tax
                order.shipping = shipping
                order.discount = discount
                order.total = total
                order.status = random_order_status()

        print(f"Seeded {number_of_orders} orders.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_orders()