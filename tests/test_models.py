"""Tests for models module."""

import pytest
from pydantic import ValidationError

from http_py.models import (
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
    PaginationMetadata,
    SuccessResponse,
)


def test_success_response() -> None:
    """Test SuccessResponse model."""
    response = SuccessResponse(data={"id": 1, "name": "test"})
    assert response.success is True
    assert response.data == {"id": 1, "name": "test"}
    assert response.message is None


def test_success_response_with_message() -> None:
    """Test SuccessResponse with message."""
    response = SuccessResponse(data={"id": 1}, message="Created successfully")
    assert response.success is True
    assert response.message == "Created successfully"


def test_error_detail() -> None:
    """Test ErrorDetail model."""
    detail = ErrorDetail(field="email", message="Invalid email", code="INVALID_EMAIL")
    assert detail.field == "email"
    assert detail.message == "Invalid email"
    assert detail.code == "INVALID_EMAIL"


def test_error_response() -> None:
    """Test ErrorResponse model."""
    response = ErrorResponse(error="Not found", status_code=404)
    assert response.success is False
    assert response.error == "Not found"
    assert response.status_code == 404
    assert response.details is None


def test_error_response_with_details() -> None:
    """Test ErrorResponse with details."""
    details = [
        ErrorDetail(field="email", message="Invalid email"),
        ErrorDetail(field="password", message="Too short"),
    ]
    response = ErrorResponse(error="Validation failed", status_code=422, details=details)
    assert response.success is False
    assert response.details is not None
    assert len(response.details) == 2


def test_pagination_metadata() -> None:
    """Test PaginationMetadata model."""
    pagination = PaginationMetadata(
        page=1,
        page_size=10,
        total_items=100,
        total_pages=10,
    )
    assert pagination.page == 1
    assert pagination.page_size == 10
    assert pagination.total_items == 100
    assert pagination.total_pages == 10


def test_pagination_metadata_validation() -> None:
    """Test PaginationMetadata validation."""
    with pytest.raises(ValidationError):
        PaginationMetadata(page=0, page_size=10, total_items=100, total_pages=10)

    with pytest.raises(ValidationError):
        PaginationMetadata(page=1, page_size=0, total_items=100, total_pages=10)


def test_paginated_response() -> None:
    """Test PaginatedResponse model."""
    pagination = PaginationMetadata(
        page=1,
        page_size=10,
        total_items=100,
        total_pages=10,
    )
    data = [{"id": 1}, {"id": 2}, {"id": 3}]
    response = PaginatedResponse(data=data, pagination=pagination)

    assert response.success is True
    assert len(response.data) == 3
    assert response.pagination.page == 1
    assert response.message is None


def test_generic_typing() -> None:
    """Test generic typing support."""
    # Test with different types
    str_response = SuccessResponse[str](data="test")
    assert str_response.data == "test"

    dict_response = SuccessResponse[dict[str, int]](data={"count": 5})
    assert dict_response.data == {"count": 5}

    list_response = SuccessResponse[list[int]](data=[1, 2, 3])
    assert list_response.data == [1, 2, 3]
