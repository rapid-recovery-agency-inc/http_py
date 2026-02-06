"""Tests for utils module."""

from http_py.constants import HTTPStatus
from http_py.models import ErrorDetail
from http_py.utils import (
    calculate_offset,
    create_error_response,
    create_paginated_response,
    create_success_response,
    extract_bearer_token,
)


def test_create_success_response() -> None:
    """Test create_success_response."""
    data = {"id": 1, "name": "test"}
    result = create_success_response(data)

    assert result["success"] is True
    assert result["data"] == data
    assert "message" not in result


def test_create_success_response_with_message() -> None:
    """Test create_success_response with message."""
    data = {"id": 1}
    result = create_success_response(data, message="Created successfully")

    assert result["success"] is True
    assert result["message"] == "Created successfully"


def test_create_error_response() -> None:
    """Test create_error_response."""
    result = create_error_response("Not found", status_code=404)

    assert result["success"] is False
    assert result["error"] == "Not found"
    assert result["status_code"] == 404
    assert "details" not in result


def test_create_error_response_with_details() -> None:
    """Test create_error_response with details."""
    details = [
        ErrorDetail(field="email", message="Invalid email"),
    ]
    result = create_error_response("Validation error", status_code=422, details=details)

    assert result["success"] is False
    assert result["error"] == "Validation error"
    assert result["status_code"] == 422
    assert "details" in result
    assert len(result["details"]) == 1


def test_create_error_response_default_status() -> None:
    """Test create_error_response with default status code."""
    result = create_error_response("Something went wrong")

    assert result["status_code"] == HTTPStatus.INTERNAL_SERVER_ERROR


def test_create_paginated_response() -> None:
    """Test create_paginated_response."""
    data = [{"id": 1}, {"id": 2}, {"id": 3}]
    result = create_paginated_response(
        data=data,
        page=1,
        page_size=10,
        total_items=100,
    )

    assert result["success"] is True
    assert result["data"] == data
    assert result["pagination"]["page"] == 1
    assert result["pagination"]["page_size"] == 10
    assert result["pagination"]["total_items"] == 100
    assert result["pagination"]["total_pages"] == 10


def test_create_paginated_response_with_message() -> None:
    """Test create_paginated_response with message."""
    result = create_paginated_response(
        data=[],
        page=1,
        page_size=10,
        total_items=0,
        message="No results found",
    )

    assert result["message"] == "No results found"


def test_create_paginated_response_total_pages_calculation() -> None:
    """Test total_pages calculation in create_paginated_response."""
    # Test exact division
    result = create_paginated_response(
        data=[],
        page=1,
        page_size=10,
        total_items=100,
    )
    assert result["pagination"]["total_pages"] == 10

    # Test with remainder
    result = create_paginated_response(
        data=[],
        page=1,
        page_size=10,
        total_items=95,
    )
    assert result["pagination"]["total_pages"] == 10

    # Test with zero items
    result = create_paginated_response(
        data=[],
        page=1,
        page_size=10,
        total_items=0,
    )
    assert result["pagination"]["total_pages"] == 0


def test_calculate_offset() -> None:
    """Test calculate_offset."""
    assert calculate_offset(page=1, page_size=10) == 0
    assert calculate_offset(page=2, page_size=10) == 10
    assert calculate_offset(page=3, page_size=10) == 20
    assert calculate_offset(page=1, page_size=25) == 0
    assert calculate_offset(page=5, page_size=25) == 100


def test_extract_bearer_token() -> None:
    """Test extract_bearer_token."""
    # Valid token
    token = extract_bearer_token("Bearer abc123xyz")
    assert token == "abc123xyz"

    # No authorization header
    token = extract_bearer_token(None)
    assert token is None

    # Invalid format - not Bearer
    token = extract_bearer_token("Basic abc123")
    assert token is None

    # Invalid format - wrong number of parts
    token = extract_bearer_token("Bearer")
    assert token is None

    # Case insensitive
    token = extract_bearer_token("bearer abc123xyz")
    assert token == "abc123xyz"

    # Token with special characters
    token = extract_bearer_token("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test")
    assert token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"
