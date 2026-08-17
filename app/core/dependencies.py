from app.providers.payment.mock import MockPaymentProvider
from app.providers.payment.base import PaymentGateway


def get_payment_provider() -> PaymentGateway:
    return MockPaymentProvider()