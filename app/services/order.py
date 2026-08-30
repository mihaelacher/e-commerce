
from sqlalchemy.orm import Session

from app.exceptions import product
from app.exceptions.checkout import OrderNotFoundError
from app.models.order import OrderModel
from app.repositories.order import OrderRepository


def get_order(
    db: Session,
    order_id: int,
) -> OrderModel:
    repository = OrderRepository(db)

    order = repository.get(order_id)

    if order is None:
        raise OrderNotFoundError(order_id)

    return order
