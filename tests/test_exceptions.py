"""Tests for exceptions module."""

from http_py.constants import HTTPStatus
from http_py.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    HTTPException,
    InternalServerErrorException,
    MethodNotAllowedException,
    NotFoundException,
    ServiceUnavailableException,
    TooManyRequestsException,
    UnauthorizedException,
    UnprocessableEntityException,
    http_exception_handler,
)
from http_py.models import ErrorDetail


def test_http_exception() -> None:
    """Test base HTTPException."""
    exc = HTTPException(status_code=500, message="Server error")
    assert exc.status_code == 500
    assert exc.message == "Server error"
    assert exc.details is None
    assert str(exc) == "500: Server error"


def test_http_exception_with_details() -> None:
    """Test HTTPException with details."""
    details = [ErrorDetail(field="email", message="Invalid")]
    exc = HTTPException(status_code=400, message="Validation error", details=details)
    assert exc.details is not None
    assert len(exc.details) == 1


def test_bad_request_exception() -> None:
    """Test BadRequestException."""
    exc = BadRequestException()
    assert exc.status_code == HTTPStatus.BAD_REQUEST
    assert exc.message == "Bad Request"


def test_unauthorized_exception() -> None:
    """Test UnauthorizedException."""
    exc = UnauthorizedException(message="Invalid token")
    assert exc.status_code == HTTPStatus.UNAUTHORIZED
    assert exc.message == "Invalid token"


def test_forbidden_exception() -> None:
    """Test ForbiddenException."""
    exc = ForbiddenException()
    assert exc.status_code == HTTPStatus.FORBIDDEN
    assert exc.message == "Forbidden"


def test_not_found_exception() -> None:
    """Test NotFoundException."""
    exc = NotFoundException(message="User not found")
    assert exc.status_code == HTTPStatus.NOT_FOUND
    assert exc.message == "User not found"


def test_method_not_allowed_exception() -> None:
    """Test MethodNotAllowedException."""
    exc = MethodNotAllowedException()
    assert exc.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert exc.message == "Method Not Allowed"


def test_conflict_exception() -> None:
    """Test ConflictException."""
    exc = ConflictException(message="Email already exists")
    assert exc.status_code == HTTPStatus.CONFLICT
    assert exc.message == "Email already exists"


def test_unprocessable_entity_exception() -> None:
    """Test UnprocessableEntityException."""
    exc = UnprocessableEntityException()
    assert exc.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert exc.message == "Unprocessable Entity"


def test_too_many_requests_exception() -> None:
    """Test TooManyRequestsException."""
    exc = TooManyRequestsException()
    assert exc.status_code == HTTPStatus.TOO_MANY_REQUESTS
    assert exc.message == "Too Many Requests"


def test_internal_server_error_exception() -> None:
    """Test InternalServerErrorException."""
    exc = InternalServerErrorException()
    assert exc.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert exc.message == "Internal Server Error"


def test_service_unavailable_exception() -> None:
    """Test ServiceUnavailableException."""
    exc = ServiceUnavailableException()
    assert exc.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert exc.message == "Service Unavailable"


def test_http_exception_handler() -> None:
    """Test http_exception_handler."""
    exc = NotFoundException(message="Resource not found")
    result = http_exception_handler(exc)

    assert result["success"] is False
    assert result["error"] == "Resource not found"
    assert result["status_code"] == 404
    assert "details" not in result


def test_http_exception_handler_with_details() -> None:
    """Test http_exception_handler with details."""
    details = [
        ErrorDetail(field="email", message="Invalid email"),
        ErrorDetail(field="password", message="Too short"),
    ]
    exc = BadRequestException(message="Validation failed", details=details)
    result = http_exception_handler(exc)

    assert result["success"] is False
    assert result["error"] == "Validation failed"
    assert result["status_code"] == 400
    assert "details" in result
    assert len(result["details"]) == 2
    assert result["details"][0]["field"] == "email"
