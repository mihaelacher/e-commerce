from enum import StrEnum


class OrderStatus(StrEnum):
    PENDING = "pending"
    PAYMENT_PENDING = "payment_pending"
    PAID = "paid"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    CANCELLATION_PENDING = "cancellation_pending"
