"""Exception handling module for HTTP APIs.

Provides a declarative approach to building unified FastAPI exception handlers.
"""

from http_py.exceptions.types import (
    HandlerRule,
    ContentBuilderFn,
    FastAPIRequestValidationError,
)
from http_py.exceptions.utils import (
    build_unexpected_content,
    build_validation_content,
    build_client_error_content,
)
from http_py.exceptions.services import (
    get_request_metadata,
    create_exception_handlers,
)


__all__ = [
    "ContentBuilderFn",
    "FastAPIRequestValidationError",
    "HandlerRule",
    "build_client_error_content",
    "build_unexpected_content",
    "build_validation_content",
    "create_exception_handlers",
    "get_request_metadata",
]
