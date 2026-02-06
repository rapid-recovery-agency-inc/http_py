"""Standardized request and response models."""

from typing import TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse[T](BaseModel):
    """Standardized success response model.

    Args:
        success: Always True for success responses.
        data: The response data.
        message: Optional success message.
    """

    success: bool = Field(default=True, description="Indicates successful response")
    data: T = Field(..., description="Response data")
    message: str | None = Field(default=None, description="Optional success message")


class ErrorDetail(BaseModel):
    """Detailed error information.

    Args:
        field: The field that caused the error (optional).
        message: Error message describing the issue.
        code: Optional error code for programmatic handling.
    """

    field: str | None = Field(default=None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: str | None = Field(default=None, description="Error code")


class ErrorResponse(BaseModel):
    """Standardized error response model.

    Args:
        success: Always False for error responses.
        error: Error message.
        details: Optional list of detailed error information.
        status_code: HTTP status code.
    """

    success: bool = Field(default=False, description="Indicates error response")
    error: str = Field(..., description="Error message")
    details: list[ErrorDetail] | None = Field(
        default=None, description="Detailed error information"
    )
    status_code: int = Field(..., description="HTTP status code")


class PaginationMetadata(BaseModel):
    """Pagination metadata for list responses.

    Args:
        page: Current page number (1-indexed).
        page_size: Number of items per page.
        total_items: Total number of items.
        total_pages: Total number of pages.
    """

    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


class PaginatedResponse[T](BaseModel):
    """Standardized paginated response model.

    Args:
        success: Always True for success responses.
        data: List of items for current page.
        pagination: Pagination metadata.
        message: Optional success message.
    """

    success: bool = Field(default=True, description="Indicates successful response")
    data: list[T] = Field(..., description="List of items")
    pagination: PaginationMetadata = Field(..., description="Pagination metadata")
    message: str | None = Field(default=None, description="Optional success message")
