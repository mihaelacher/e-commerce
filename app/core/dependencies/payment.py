from app.providers.payment.base import PaymentGateway
from app.providers.payment.mock import MockPaymentProvider


def get_payment_provider() -> PaymentGateway:
    return MockPaymentProvider()
