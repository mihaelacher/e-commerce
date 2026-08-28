from fastapi import FastAPI

from app.exceptions.ai import AIProviderUnavailableError
from app.exceptions.checkout import (
    EmptyOrderError,
    InsufficientStockError,
    OrderAlreadyProcessedError,
    OrderItemNotFoundError,
    OrderNotFoundError,
)
from app.exceptions.handlers import (
    ai_provider_unavailable_handler,
    empty_order_handler,
    insufficient_stock_handler,
    order_already_processed_handler,
    order_cannot_be_paid_handler,
    order_item_not_found_handler,
    order_not_found_handler,
    payment_not_found_handler,
    product_not_found_handler,
)
from app.exceptions.payment import OrderCannotBePaidError, PaymentNotFoundError
from app.exceptions.product import ProductNotFoundError
from app.routers import checkout, product, payment, analytics, ai


def create_app() -> FastAPI:
    app = FastAPI(
        title="E-Commerce API",
        version="1.0.0",
    )

    app.include_router(product.router)
    app.include_router(checkout.router)
    app.include_router(payment.router)
    app.include_router(analytics.router)
    app.include_router(ai.router)

    app.add_exception_handler(
        ProductNotFoundError,
        product_not_found_handler,
    )
    app.add_exception_handler(
        OrderNotFoundError,
        order_not_found_handler,
    )
    app.add_exception_handler(
        OrderItemNotFoundError,
        order_item_not_found_handler,
    )
    app.add_exception_handler(
        InsufficientStockError,
        insufficient_stock_handler,
    )
    app.add_exception_handler(
        EmptyOrderError,
        empty_order_handler,
    )
    app.add_exception_handler(
        OrderAlreadyProcessedError,
        order_already_processed_handler,
    )
    app.add_exception_handler(
        OrderCannotBePaidError,
        order_cannot_be_paid_handler,
    )
    app.add_exception_handler(
        PaymentNotFoundError,
        payment_not_found_handler
    )
    app.add_exception_handler(
        AIProviderUnavailableError,
        ai_provider_unavailable_handler
    )
    

    return app


app = create_app()
