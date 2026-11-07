import logging
from contextvars import ContextVar

from app.core.config import settings

logger = logging.getLogger("ecommerce_api")

request_id_context: ContextVar[str] = ContextVar(
    "request_id",
    default="-",
)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_context.get()
        return True


def configure_logging() -> None:
    log_level = getattr(
        logging,
        settings.log_level.upper(),
        logging.INFO,
    )

    logging.basicConfig(
        level=log_level,
        format=(
            "%(asctime)s %(levelname)s %(name)s [request_id=%(request_id)s] %(message)s"
        ),
    )

    root_logger = logging.getLogger()

    request_context_filter = RequestContextFilter()

    for handler in root_logger.handlers:
        handler.addFilter(request_context_filter)

    logger.setLevel(log_level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def capture_exception(
    exc: Exception,
    **context,
) -> None:
    if not settings.sentry_dsn:
        return

    try:
        import sentry_sdk

        with sentry_sdk.new_scope() as scope:
            if context:
                scope.set_context(
                    "context",
                    context,
                )

            sentry_sdk.capture_exception(exc)

    except Exception as sentry_exc:  # noqa: BLE001
        logger.warning(
            "sentry_capture_failed",
            extra={
                "error": str(sentry_exc),
            },
        )


def setup_error_tracking() -> None:
    if not settings.sentry_dsn:
        return

    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=0.1,
        )
    except Exception as sentry_exc:  # noqa: BLE001
        logger.warning(
            "sentry_init_failed",
            extra={"error": str(sentry_exc)},
        )
