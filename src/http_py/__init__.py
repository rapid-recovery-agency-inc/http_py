"""http-py: A minimalistic library for sharing HTTP code between Python APIs and microservices."""

from http_py.constants import ContentType, HTTPHeader, HTTPMethod, HTTPStatus
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
from http_py.middleware import CORSMiddleware, LoggingMiddleware
from http_py.models import ErrorResponse, SuccessResponse
from http_py.utils import (
    calculate_offset,
    create_error_response,
    create_paginated_response,
    create_success_response,
    extract_bearer_token,
)

__version__ = "0.1.0"

__all__ = [
    # Constants
    "ContentType",
    "HTTPHeader",
    "HTTPMethod",
    "HTTPStatus",
    # Exceptions
    "HTTPException",
    "BadRequestException",
    "UnauthorizedException",
    "ForbiddenException",
    "NotFoundException",
    "MethodNotAllowedException",
    "ConflictException",
    "UnprocessableEntityException",
    "TooManyRequestsException",
    "InternalServerErrorException",
    "ServiceUnavailableException",
    "http_exception_handler",
    # Models
    "ErrorResponse",
    "SuccessResponse",
    # Utils
    "create_error_response",
    "create_success_response",
    "create_paginated_response",
    "calculate_offset",
    "extract_bearer_token",
    # Middleware
    "CORSMiddleware",
    "LoggingMiddleware",
]
