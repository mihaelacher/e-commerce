class OrderCannotBePaidError(Exception):
    def __init__(self, order_id: int):
        self.order_id = order_id
        super().__init__(f"Order {order_id} cannot be paid")


class PaymentNotFoundError(Exception):
    def __init__(self, transaction_id: int):
        self.transaction_id = transaction_id
        super().__init__(f"Payment {transaction_id} cannot be found")
