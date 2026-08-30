import logging
from typing import Any

from app.core.config import settings


logger = logging.getLogger("ecommerce_api")


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def capture_exception(exc: Exception, **context: Any) -> None:
    if settings.sentry_dsn:
        try:
            import sentry_sdk

            if context:
                sentry_sdk.set_context("context", context)
            sentry_sdk.capture_exception(exc)
        except Exception:
            pass

    logger.exception("captured_exception", extra={"context": context})


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
    except Exception:
        pass
