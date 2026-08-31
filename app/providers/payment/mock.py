import random
import uuid
from decimal import Decimal

from app.enums.payment_provider import PaymentProvider
from app.providers.payment.base import PaymentResult


class MockPaymentProvider:
    type = PaymentProvider.MOCK

    def __init__(self, should_succeed: bool | None = None):
        self.should_succeed = should_succeed

    def charge(
        self,
        amount: Decimal,
        idempotency_key: str,
    ) -> PaymentResult:
        #time.sleep(2)
        
        success = (
            self.should_succeed
            if self.should_succeed is not None
            else random.choice([True, False])
        )

        return PaymentResult(
            success=success,
            transaction_id = f"mock_{uuid.uuid4()}"
        )


    def parse_webhook(
        self,
        data: dict,
    ) -> PaymentResult:
        if data["status"] == "success":
            return PaymentResult(
                success=True,
                transaction_id=data["transaction_id"],
            )

        return PaymentResult(
            success=False,
            transaction_id=data["transaction_id"],
        )


    def verify_webhook(
            self, 
            data: dict,
            signature: str,
        ) -> bool:
        return (
            isinstance(data, dict)
            and "status" in data
            and "transaction_id" in data
        )