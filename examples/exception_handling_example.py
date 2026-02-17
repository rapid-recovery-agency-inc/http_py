"""Examples: http_py.exception_handling module usage.

This example demonstrates declarative exception handler creation
for building unified FastAPI exception handlers.
"""

from typing import Any, Final

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

from http_py.exception_handling import (
    HandlerRule,
    build_unexpected_content,
    build_validation_content,
    create_exception_handler,
    build_client_error_content,
)


# ──────────────────────────────────────────────────────────────────────
# 1. Define Your Application Exceptions
# ──────────────────────────────────────────────────────────────────────


class TaskDoesNotExistException(Exception):
    """Task not found."""

    pass


class DataSourceFetchException(Exception):
    """Failed to fetch data from external source."""

    pass


class NoLocationsFoundException(Exception):
    """No locations found for processing."""

    pass


class FailedLockAcquisitionException(Exception):
    """Could not acquire distributed lock."""

    pass


class ScoringEngineBaseException(Exception):
    """Base exception for scoring engine errors."""

    pass


# Mock AWS ClientError for example
class ClientError(Exception):
    """AWS client error."""

    def __init__(self, message: str, response: dict | None = None):
        super().__init__(message)
        self.response = response or {}


# ──────────────────────────────────────────────────────────────────────
# 2. Define Handler Rules (exception -> response mapping)
# ──────────────────────────────────────────────────────────────────────

HANDLER_MAP: Final[dict[str, HandlerRule]] = {
    # 422 - Validation errors (custom content builder)
    "validation": HandlerRule(
        RequestValidationError,
        status_code=422,
        content_builder=build_validation_content,
    ),
    # 404 - Not Found
    "task_not_found": HandlerRule(
        TaskDoesNotExistException,
        status_code=404,
    ),
    # 400 - Bad Request (don't include exception detail)
    "data_source_error": HandlerRule(
        DataSourceFetchException,
        status_code=400,
        include_detail=False,
    ),
    # 200 - Expected business conditions (prevent SQS retry)
    "no_locations": HandlerRule(
        NoLocationsFoundException,
        status_code=200,
        log_level="debug",
        include_detail=False,
    ),
    # 423 - Locked
    "lock_failure": HandlerRule(
        FailedLockAcquisitionException,
        status_code=423,
        log_level="warning",
    ),
    # 500 - AWS errors (custom content builder)
    "client_error": HandlerRule(
        ClientError,
        status_code=500,
        content_builder=build_client_error_content,
    ),
    # 500 - Application errors
    "scoring_engine_base": HandlerRule(
        ScoringEngineBaseException,
        status_code=500,
    ),
    # 500 - True catch-all (must be LAST)
    "unexpected": HandlerRule(
        Exception,
        status_code=500,
        log_level="critical",
        content_builder=build_unexpected_content,
    ),
}


# ──────────────────────────────────────────────────────────────────────
# 3. FastAPI Integration
# ──────────────────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    """Create FastAPI app with unified exception handler."""
    app = FastAPI()

    # Create single handler for all exceptions
    exception_handler = create_exception_handler(handler_map=HANDLER_MAP)

    # Register for validation errors and all exceptions
    app.add_exception_handler(RequestValidationError, exception_handler)
    app.add_exception_handler(Exception, exception_handler)

    return app


# ──────────────────────────────────────────────────────────────────────
# 4. HandlerRule Parameters
# ──────────────────────────────────────────────────────────────────────

# HandlerRule(
#     exc_type: type[Exception],       # Exception class to match
#     status_code: int,                # HTTP status code
#     log_level: str | None = "error", # "debug"|"info"|...|"critical"|None
#     include_detail: bool = True,     # Include str(exc) in response
#     content_builder: fn | None,      # Custom async content builder
# )


# ──────────────────────────────────────────────────────────────────────
# 5. Custom Content Builder
# ──────────────────────────────────────────────────────────────────────


async def build_custom_error_content(
    request: Request, exc: Exception, meta: dict[str, str]
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Example custom content builder.

    Args:
        request: The Starlette request
        exc: The caught exception
        meta: Dict with request_id, path, method

    Returns:
        (response_content, log_extras)
    """
    content = {
        "error": "custom_error",
        "message": str(exc),
        **meta,
    }
    log_extras = {
        "custom_field": "value",
    }
    return content, log_extras
