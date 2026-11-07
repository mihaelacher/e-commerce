class OrderNotFoundError(Exception):
    def __init__(self, order_id: int):
        self.order_id = order_id
        super().__init__(f"Order {order_id} not found")


class OrderItemNotFoundError(Exception):
    def __init__(self, item_id: int):
        self.item_id = item_id
        super().__init__(f"Order item {item_id} not found")


class OrderAlreadyProcessedError(Exception):
    def __init__(self, order_id: int):
        super().__init__(f"Order {order_id} has already been processed")


class InsufficientStockError(Exception):
    def __init__(
        self,
        product_id: int,
        requested: int,
        available: int,
    ):
        super().__init__(
            f"Insufficient stock for product {product_id}. "
            f"Requested {requested}, available {available}."
        )


class EmptyOrderError(Exception):
    def __init__(self, order_id: int):
        super().__init__(f"Order {order_id} is empty and cannot be processed.")
