import logging

from app.core.logging import (
    RequestContextFilter,
    request_id_context,
)


def test_request_id_is_added_to_response(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert "X-Request-Id" in response.headers
    assert response.headers["X-Request-Id"]


def test_request_context_filter_adds_request_id():
    token = request_id_context.set("test-request-id")

    try:
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )

        log_filter = RequestContextFilter()

        assert log_filter.filter(record) is True
        assert record.request_id == "test-request-id"
    finally:
        request_id_context.reset(token)
