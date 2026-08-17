class OrderCannotBePaidError(Exception):
    def __init__(self, order_id: int):
        self.order_id = order_id
        super().__init__(f"Order {order_id} cannot be paid")