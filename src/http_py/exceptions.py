"""HTTP exceptions and error handling utilities."""

from typing import Any

from http_py.constants import HTTPStatus
from http_py.models import ErrorDetail


class HTTPException(Exception):
    """Base HTTP exception class.

    Args:
        status_code: HTTP status code.
        message: Error message.
        details: Optional list of detailed error information.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        """Initialize HTTPException."""
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(message)

    def __str__(self) -> str:
        """String representation of the exception."""
        return f"{self.status_code}: {self.message}"


class BadRequestException(HTTPException):
    """400 Bad Request exception."""

    def __init__(
        self, message: str = "Bad Request", details: list[ErrorDetail] | None = None
    ) -> None:
        """Initialize BadRequestException."""
        super().__init__(HTTPStatus.BAD_REQUEST, message, details)


class UnauthorizedException(HTTPException):
    """401 Unauthorized exception."""

    def __init__(
        self, message: str = "Unauthorized", details: list[ErrorDetail] | None = None
    ) -> None:
        """Initialize UnauthorizedException."""
        super().__init__(HTTPStatus.UNAUTHORIZED, message, details)


class ForbiddenException(HTTPException):
    """403 Forbidden exception."""

    def __init__(
        self, message: str = "Forbidden", details: list[ErrorDetail] | None = None
    ) -> None:
        """Initialize ForbiddenException."""
        super().__init__(HTTPStatus.FORBIDDEN, message, details)


class NotFoundException(HTTPException):
    """404 Not Found exception."""

    def __init__(
        self, message: str = "Not Found", details: list[ErrorDetail] | None = None
    ) -> None:
        """Initialize NotFoundException."""
        super().__init__(HTTPStatus.NOT_FOUND, message, details)


class MethodNotAllowedException(HTTPException):
    """405 Method Not Allowed exception."""

    def __init__(
        self,
        message: str = "Method Not Allowed",
        details: list[ErrorDetail] | None = None,
    ) -> None:
        """Initialize MethodNotAllowedException."""
        super().__init__(HTTPStatus.METHOD_NOT_ALLOWED, message, details)


class ConflictException(HTTPException):
    """409 Conflict exception."""

    def __init__(
        self, message: str = "Conflict", details: list[ErrorDetail] | None = None
    ) -> None:
        """Initialize ConflictException."""
        super().__init__(HTTPStatus.CONFLICT, message, details)


class UnprocessableEntityException(HTTPException):
    """422 Unprocessable Entity exception."""

    def __init__(
        self,
        message: str = "Unprocessable Entity",
        details: list[ErrorDetail] | None = None,
    ) -> None:
        """Initialize UnprocessableEntityException."""
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message, details)


class TooManyRequestsException(HTTPException):
    """429 Too Many Requests exception."""

    def __init__(
        self,
        message: str = "Too Many Requests",
        details: list[ErrorDetail] | None = None,
    ) -> None:
        """Initialize TooManyRequestsException."""
        super().__init__(HTTPStatus.TOO_MANY_REQUESTS, message, details)


class InternalServerErrorException(HTTPException):
    """500 Internal Server Error exception."""

    def __init__(
        self,
        message: str = "Internal Server Error",
        details: list[ErrorDetail] | None = None,
    ) -> None:
        """Initialize InternalServerErrorException."""
        super().__init__(HTTPStatus.INTERNAL_SERVER_ERROR, message, details)


class ServiceUnavailableException(HTTPException):
    """503 Service Unavailable exception."""

    def __init__(
        self,
        message: str = "Service Unavailable",
        details: list[ErrorDetail] | None = None,
    ) -> None:
        """Initialize ServiceUnavailableException."""
        super().__init__(HTTPStatus.SERVICE_UNAVAILABLE, message, details)


def http_exception_handler(exc: HTTPException) -> dict[str, Any]:
    """Convert HTTPException to a dictionary for JSON response.

    Args:
        exc: The HTTPException to convert.

    Returns:
        Dictionary containing error details.
    """
    response: dict[str, Any] = {
        "success": False,
        "error": exc.message,
        "status_code": exc.status_code,
    }

    if exc.details:
        response["details"] = [detail.model_dump() for detail in exc.details]

    return response
