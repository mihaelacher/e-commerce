from app.enums.order import OrderStatus


class OrderCannotBeCancelledError(Exception):
    def __init__(
        self,
        order_id: int,
        status: OrderStatus,
    ):
        super().__init__(
            f"Order {order_id} with status '{status}' cannot be cancelled."
        )


class PaidOrderPaymentNotFoundError(Exception):
    def __init__(self, order_id: int):
        super().__init__(f"Paid payment not found for paid order {order_id}.")
