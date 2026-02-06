"""Utility functions for HTTP operations."""

from typing import Any, TypeVar

from http_py.constants import HTTPStatus
from http_py.models import (
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
    PaginationMetadata,
    SuccessResponse,
)

T = TypeVar("T")


def create_success_response[T](
    data: T, message: str | None = None
) -> dict[str, Any]:
    """Create a standardized success response.

    Args:
        data: The response data.
        message: Optional success message.

    Returns:
        Dictionary containing the success response.
    """
    response = SuccessResponse(data=data, message=message)
    return response.model_dump(exclude_none=True)


def create_error_response(
    error: str,
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
    details: list[ErrorDetail] | None = None,
) -> dict[str, Any]:
    """Create a standardized error response.

    Args:
        error: Error message.
        status_code: HTTP status code.
        details: Optional list of detailed error information.

    Returns:
        Dictionary containing the error response.
    """
    response = ErrorResponse(
        error=error,
        status_code=status_code,
        details=details,
    )
    return response.model_dump(exclude_none=True)


def create_paginated_response[T](
    data: list[T],
    page: int,
    page_size: int,
    total_items: int,
    message: str | None = None,
) -> dict[str, Any]:
    """Create a standardized paginated response.

    Args:
        data: List of items for the current page.
        page: Current page number (1-indexed).
        page_size: Number of items per page.
        total_items: Total number of items.
        message: Optional success message.

    Returns:
        Dictionary containing the paginated response.
    """
    total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 0

    pagination = PaginationMetadata(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )

    response = PaginatedResponse(
        data=data,
        pagination=pagination,
        message=message,
    )
    return response.model_dump(exclude_none=True)


def calculate_offset(page: int, page_size: int) -> int:
    """Calculate offset for database queries from page and page_size.

    Args:
        page: Current page number (1-indexed).
        page_size: Number of items per page.

    Returns:
        Offset value for database query.
    """
    return (page - 1) * page_size


def extract_bearer_token(authorization: str | None) -> str | None:
    """Extract bearer token from Authorization header.

    Args:
        authorization: Authorization header value.

    Returns:
        Bearer token if found, None otherwise.
    """
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]
