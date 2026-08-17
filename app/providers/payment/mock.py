import random
from decimal import Decimal
import uuid

from app.providers.payment.base import PaymentResult


class MockPaymentProvider:
    def __init__(self, should_succeed: bool | None = None):
        self.should_succeed = should_succeed

    def charge(
        self,
        amount: Decimal,
        idempotency_key: str,
    ) -> PaymentResult:
        success = (
            self.should_succeed
            if self.should_succeed is not None
            else random.choice([True, False])
        )

        if not success:
            return PaymentResult(success=False)

        return PaymentResult(
            success=True,
            transaction_id = f"mock_{uuid.uuid4()}"
        )