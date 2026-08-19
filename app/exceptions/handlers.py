from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.exceptions.checkout import (
    EmptyOrderError,
    InsufficientStockError,
    OrderAlreadyProcessedError,
    OrderItemNotFoundError,
    OrderNotFoundError,
)
from app.exceptions.product import ProductNotFoundError
from app.exceptions.payment import OrderCannotBePaidError, PaymentNotFoundError


async def product_not_found_handler(
    _: Request,
    exc: ProductNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


async def order_not_found_handler(
    _: Request,
    exc: OrderNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


async def order_item_not_found_handler(
    _: Request,
    exc: OrderItemNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


async def insufficient_stock_handler(
    _: Request,
    exc: InsufficientStockError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


async def empty_order_handler(
    _: Request,
    exc: EmptyOrderError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


async def order_already_processed_handler(
    _: Request,
    exc: OrderAlreadyProcessedError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


async def order_cannot_be_paid_handler(
    _: Request,
    exc: OrderCannotBePaidError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


async def payment_not_found_handler(
    _: Request,
    exc: PaymentNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )