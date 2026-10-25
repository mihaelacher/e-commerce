import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from redis.asyncio import Redis

from app.core.config import settings
from app.core.database import async_engine
from app.core.logging import (
    capture_exception,
    configure_logging,
    get_logger,
    request_id_context,
    setup_error_tracking,
)
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
    pending_action_not_found_handler,
    pending_action_unsupported_handler,
    product_not_found_handler,
)
from app.exceptions.payment import OrderCannotBePaidError, PaymentNotFoundError
from app.exceptions.pending_action import (
    PendingActionNotFoundError,
    UnsupportedPendingActionError,
)
from app.exceptions.product import ProductNotFoundError
from app.routers import (
    ai,
    analytics,
    checkout,
    order,
    payment,
    pending_actions,
    product,
)

configure_logging()
setup_error_tracking()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )

    async with AsyncPostgresSaver.from_conn_string(
        settings.connection_url,
    ) as checkpointer:
        await checkpointer.setup()

        app.state.redis = redis
        app.state.langgraph_checkpointer = checkpointer

        yield

    await redis.aclose()
    await async_engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="E-Commerce API",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def request_logging_middleware(
        request: Request,
        call_next,
    ):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        token = request_id_context.set(request_id)

        start_time = time.perf_counter()

        try:
            response = await call_next(request)

            duration_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2,
            )

            logger.info(
                "request_completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

            response.headers["X-Request-Id"] = request_id
            return response
        finally:
            request_id_context.reset(token)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ):
        request_id = getattr(
            request.state,
            "request_id",
            "unknown",
        )

        logger.exception(
            "unhandled_exception",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            },
        )

        capture_exception(
            exc,
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal Server Error",
            },
            headers={
                "X-Request-Id": request_id,
            },
        )

    app.include_router(product.router)
    app.include_router(order.router)
    app.include_router(checkout.router)
    app.include_router(payment.router)
    app.include_router(analytics.router)
    app.include_router(ai.router)
    app.include_router(pending_actions.router)

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
        payment_not_found_handler,
    )
    app.add_exception_handler(
        AIProviderUnavailableError,
        ai_provider_unavailable_handler,
    )
    app.add_exception_handler(
        PendingActionNotFoundError,
        pending_action_not_found_handler,
    )
    app.add_exception_handler(
        UnsupportedPendingActionError,
        pending_action_unsupported_handler,
    )

    return app


app = create_app()
