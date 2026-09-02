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
    ) -> PaymentResult: ...

    def refund(
        self,
        transaction_id: str,
        amount: Decimal,
        idempotency_key: str,
    ) -> PaymentResult: ...

    def parse_webhook(
        self,
        data: dict,
    ) -> PaymentResult: ...

    def verify_webhook(
        self,
        data: dict,
        signature: str,
    ) -> bool: ...
