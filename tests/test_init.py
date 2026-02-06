"""Tests for __init__ module."""

import http_py
from http_py import (
    BadRequestException,
    ContentType,
    CORSMiddleware,
    ErrorResponse,
    HTTPException,
    HTTPHeader,
    HTTPMethod,
    HTTPStatus,
    LoggingMiddleware,
    SuccessResponse,
    calculate_offset,
    create_error_response,
    create_paginated_response,
    create_success_response,
    extract_bearer_token,
    http_exception_handler,
)


def test_version() -> None:
    """Test version is defined."""
    assert hasattr(http_py, "__version__")
    assert http_py.__version__ == "0.1.0"


def test_exports() -> None:
    """Test all expected exports are available."""
    # Constants
    assert HTTPStatus is not None
    assert HTTPMethod is not None
    assert HTTPHeader is not None
    assert ContentType is not None

    # Exceptions
    assert HTTPException is not None
    assert BadRequestException is not None
    assert http_exception_handler is not None

    # Models
    assert SuccessResponse is not None
    assert ErrorResponse is not None

    # Utils
    assert create_success_response is not None
    assert create_error_response is not None
    assert create_paginated_response is not None
    assert calculate_offset is not None
    assert extract_bearer_token is not None

    # Middleware
    assert CORSMiddleware is not None
    assert LoggingMiddleware is not None


def test_imports_work() -> None:
    """Test that imports work correctly."""
    # This test verifies that importing from the package works
    from http_py import HTTPStatus as status

    assert status.OK == 200
