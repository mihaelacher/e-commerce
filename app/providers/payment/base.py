from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass
class PaymentResult:
    success: bool
    transaction_id: str | None = None


class PaymentGateway(Protocol):
    def charge(
        self,
        amount: Decimal,
        idempotency_key: str,
    ) -> PaymentResult:
        ...