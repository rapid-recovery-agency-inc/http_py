"""http-py: A minimalistic library for sharing HTTP code between Python APIs and microservices."""

from http_py.constants import ContentType, HTTPHeader, HTTPMethod, HTTPStatus
from http_py.exceptions import HTTPException, http_exception_handler
from http_py.middleware import CORSMiddleware, LoggingMiddleware
from http_py.models import ErrorResponse, SuccessResponse
from http_py.utils import create_error_response, create_success_response

__version__ = "0.1.0"

__all__ = [
    # Constants
    "ContentType",
    "HTTPHeader",
    "HTTPMethod",
    "HTTPStatus",
    # Exceptions
    "HTTPException",
    "http_exception_handler",
    # Models
    "ErrorResponse",
    "SuccessResponse",
    # Utils
    "create_error_response",
    "create_success_response",
    # Middleware
    "CORSMiddleware",
    "LoggingMiddleware",
]
