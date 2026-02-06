"""Tests for middleware module."""

import logging

import pytest

from http_py.middleware import CORSMiddleware, LoggingMiddleware, timing_middleware


def test_cors_middleware_default() -> None:
    """Test CORSMiddleware with default values."""
    cors = CORSMiddleware()
    headers = cors.get_headers()

    assert headers["Access-Control-Allow-Origin"] == "*"
    assert "GET" in headers["Access-Control-Allow-Methods"]
    assert "POST" in headers["Access-Control-Allow-Methods"]
    assert headers["Access-Control-Allow-Headers"] == "*"
    assert headers["Access-Control-Max-Age"] == "600"


def test_cors_middleware_custom_origins() -> None:
    """Test CORSMiddleware with custom origins."""
    cors = CORSMiddleware(allow_origins=["https://example.com", "https://test.com"])
    headers = cors.get_headers(origin="https://example.com")

    assert headers["Access-Control-Allow-Origin"] == "https://example.com"


def test_cors_middleware_wildcard_origin() -> None:
    """Test CORSMiddleware with wildcard origin."""
    cors = CORSMiddleware(allow_origins="*")
    headers = cors.get_headers()

    assert headers["Access-Control-Allow-Origin"] == "*"


def test_cors_middleware_custom_methods() -> None:
    """Test CORSMiddleware with custom methods."""
    cors = CORSMiddleware(allow_methods=["GET", "POST"])
    headers = cors.get_headers()

    assert headers["Access-Control-Allow-Methods"] == "GET, POST"


def test_cors_middleware_custom_headers() -> None:
    """Test CORSMiddleware with custom headers."""
    cors = CORSMiddleware(allow_headers=["Content-Type", "Authorization"])
    headers = cors.get_headers()

    assert headers["Access-Control-Allow-Headers"] == "Content-Type, Authorization"


def test_cors_middleware_with_credentials() -> None:
    """Test CORSMiddleware with credentials."""
    cors = CORSMiddleware(allow_credentials=True)
    headers = cors.get_headers()

    assert headers["Access-Control-Allow-Credentials"] == "true"


def test_cors_middleware_without_credentials() -> None:
    """Test CORSMiddleware without credentials."""
    cors = CORSMiddleware(allow_credentials=False)
    headers = cors.get_headers()

    assert "Access-Control-Allow-Credentials" not in headers


def test_cors_middleware_max_age() -> None:
    """Test CORSMiddleware with custom max_age."""
    cors = CORSMiddleware(max_age=3600)
    headers = cors.get_headers()

    assert headers["Access-Control-Max-Age"] == "3600"


def test_logging_middleware_init() -> None:
    """Test LoggingMiddleware initialization."""
    middleware = LoggingMiddleware(
        logger_name="test",
        log_request_body=True,
        log_response_body=True,
    )

    assert middleware.logger.name == "test"
    assert middleware.log_request_body is True
    assert middleware.log_response_body is True


def test_logging_middleware_log_request(caplog: pytest.LogCaptureFixture) -> None:
    """Test LoggingMiddleware log_request."""
    with caplog.at_level(logging.INFO):
        middleware = LoggingMiddleware()
        middleware.log_request("GET", "/api/users")

        assert len(caplog.records) == 1
        assert "Incoming request" in caplog.text


def test_logging_middleware_log_request_with_headers(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test LoggingMiddleware log_request with headers."""
    with caplog.at_level(logging.INFO):
        middleware = LoggingMiddleware()
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer secret-token",
        }
        middleware.log_request("POST", "/api/users", headers=headers)

        # Check that the request was logged
        assert len(caplog.records) == 1
        # Check that authorization header was redacted in the extra data
        assert caplog.records[0].headers["Authorization"] == "***REDACTED***"
        assert caplog.records[0].headers["Content-Type"] == "application/json"


def test_logging_middleware_log_request_with_body(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test LoggingMiddleware log_request with body."""
    with caplog.at_level(logging.INFO):
        middleware = LoggingMiddleware(log_request_body=True)
        body = {"name": "test"}
        middleware.log_request("POST", "/api/users", body=body)

        assert "Incoming request" in caplog.text


def test_logging_middleware_log_response(caplog: pytest.LogCaptureFixture) -> None:
    """Test LoggingMiddleware log_response."""
    with caplog.at_level(logging.INFO):
        middleware = LoggingMiddleware()
        middleware.log_response("GET", "/api/users", 200, 150.5)

        assert len(caplog.records) == 1
        assert "Outgoing response" in caplog.text


def test_logging_middleware_log_response_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test LoggingMiddleware log_response with error status."""
    with caplog.at_level(logging.WARNING):
        middleware = LoggingMiddleware()
        middleware.log_response("GET", "/api/users", 404, 50.0)

        assert len(caplog.records) == 1


def test_timing_middleware() -> None:
    """Test timing_middleware decorator."""

    @timing_middleware
    def sample_function(x: int, y: int) -> int:
        return x + y

    result = sample_function(2, 3)
    assert result == 5


def test_timing_middleware_with_exception() -> None:
    """Test timing_middleware with exception."""

    @timing_middleware
    def failing_function() -> None:
        raise ValueError("Test error")

    try:
        failing_function()
    except ValueError as e:
        assert str(e) == "Test error"
