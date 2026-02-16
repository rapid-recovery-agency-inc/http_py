"""Exception handling module for HTTP APIs.

Provides a declarative approach to building unified FastAPI exception handlers.
"""

from http_py.exception_handling.types import (
    HandlerRule,
    ContentBuilderFn,
    FastAPIRequestValidationError,
)
from http_py.exception_handling.utils import (
    build_unexpected_content,
    build_validation_content,
    build_client_error_content,
)
from http_py.exception_handling.services import (
    get_request_metadata,
    create_exception_handler,
)


__all__ = [
    "ContentBuilderFn",
    "FastAPIRequestValidationError",
    "HandlerRule",
    "build_client_error_content",
    "build_unexpected_content",
    "build_validation_content",
    "create_exception_handler",
    "get_request_metadata",
]
