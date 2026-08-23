from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.database import transaction
from app.enums.order import OrderStatus
from app.exceptions.checkout import (
    EmptyOrderError,
    InsufficientStockError,
    OrderAlreadyProcessedError,
    OrderItemNotFoundError,
    OrderNotFoundError,
)
from app.exceptions.product import ProductNotFoundError
from app.models.order import OrderModel
from app.repositories.order import OrderRepository
from app.repositories.order_item import OrderItemRepository
from app.repositories.product import ProductRepository


def get_order_with_items(
    db: Session,
    order_id: int,
) -> OrderModel:
    repository = OrderRepository(db)
    order = repository.get_with_items(order_id)

    if order is None:
        raise OrderNotFoundError(order_id)

    return order


def create_order(
    db: Session,
    email: str,
) -> OrderModel:
    repository = OrderRepository(db)

    with transaction(db):
        return repository.create(email=email)


def _get_order_with_items(
    repository: OrderRepository,
    order_id: int,
) -> OrderModel:
    order = repository.get_with_items(order_id)

    if order is None:
        raise OrderNotFoundError(order_id)

    return order


def add_order_item(
    db: Session,
    order_id: int,
    product_id: int,
    quantity: int,
) -> OrderModel:
    order_repository = OrderRepository(db)
    product_repository = ProductRepository(db)
    order_item_repository = OrderItemRepository(db)

    with transaction(db):
        order = _get_order_with_items(order_repository, order_id)
        ensure_order_is_pending(order)

        product = product_repository.get(product_id)
        if product is None:
            raise ProductNotFoundError(product_id)

        item = order_item_repository.get_by_order_and_product(
            order_id=order.id,
            product_id=product.id,
        )

        new_quantity = item.quantity + quantity if item is not None else quantity

        if product.stock < new_quantity:
            raise InsufficientStockError(
                product_id=product.id,
                requested=new_quantity,
                available=product.stock,
            )

        if item is not None:
            item.quantity = new_quantity
            item.total_price = item.unit_price * item.quantity
        else:
            order_item_repository.create(
                order=order,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.price,
            )

        calculate_order_totals(order)
        return order


def remove_order_item(
    db: Session,
    order_id: int,
    item_id: int,
) -> OrderModel:
    order_repository = OrderRepository(db)
    order_item_repository = OrderItemRepository(db)

    with transaction(db):
        order = _get_order_with_items(order_repository, order_id)
        ensure_order_is_pending(order)

        item = order_item_repository.get(item_id)
        if item is None or item.order_id != order.id:
            raise OrderItemNotFoundError(item_id)

        order.items.remove(item)
        calculate_order_totals(order)
        return order


def decrease_order_item(
    db: Session,
    order_id: int,
    item_id: int,
) -> OrderModel:
    order_repository = OrderRepository(db)
    order_item_repository = OrderItemRepository(db)

    with transaction(db):
        order = _get_order_with_items(order_repository, order_id)
        ensure_order_is_pending(order)

        item = order_item_repository.get(item_id)
        if item is None or item.order_id != order.id:
            raise OrderItemNotFoundError(item_id)

        if item.quantity == 1:
            order.items.remove(item)
        else:
            item.quantity -= 1
            item.total_price = item.unit_price * item.quantity

        calculate_order_totals(order)
        return order


def calculate_order_totals(
    order: OrderModel,
) -> None:
    subtotal = sum(
        (item.total_price for item in order.items),
        Decimal("0.00"),
    )

    order.subtotal = subtotal
    order.tax = subtotal * Decimal("0.20")
    order.shipping = Decimal("0.00")
    order.discount = Decimal("0.00")

    order.total = order.subtotal + order.tax + order.shipping - order.discount


def checkout(
    db: Session,
    order_id: int,
) -> OrderModel:
    order_repository = OrderRepository(db)
    product_repository = ProductRepository(db)

    with transaction(db):
        order = order_repository.get_with_items_for_update(order_id)

        if order is None:
            raise OrderNotFoundError(order_id)

        ensure_order_is_pending(order)

        if not order.items:
            raise EmptyOrderError(order_id)

        for item in sorted(order.items, key=lambda item: item.product_id):
            product = product_repository.get_with_lock(item.product_id)

            if product is None:
                raise ProductNotFoundError(item.product_id)

            if product.stock < item.quantity:
                raise InsufficientStockError(
                    product_id=product.id,
                    requested=item.quantity,
                    available=product.stock,
                )

            product.stock -= item.quantity

        calculate_order_totals(order)
        order.status = OrderStatus.PAYMENT_PENDING

    return order


def ensure_order_is_pending(order: OrderModel) -> None:
    if order.status != OrderStatus.PENDING:
        raise OrderAlreadyProcessedError(order.id)
