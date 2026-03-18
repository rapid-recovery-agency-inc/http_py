"""Examples: http_py.exception_handling module usage.

This example demonstrates declarative exception handler creation
for building unified FastAPI exception handlers.
"""

from typing import Any, Final
sdfasdsadfas
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

from http_py.exceptions import HandlerRule, create_exception_handler, build_validation_content, build_client_error_content, build_unexpected_content

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

HANDLER_MAP: Final[list[HandlerRule]] = [
      # 404 - Not Found
    HandlerRule(
        TaskDoesNotExistException,
        status_code=404,
    ),
    # 422 - Validation errors (custom content builder)
    HandlerRule(
        RequestValidationError,
        status_code=422,
        content_builder=build_validation_content,
    ),
    # 400 - Bad Request (don't include exception detail)
    HandlerRule(
        DataSourceFetchException,
        status_code=400,
        include_detail=False,
    ),
    # 200 - Expected business conditions (prevent SQS retry)
    HandlerRule(
        NoLocationsFoundException,
        status_code=200,
        log_level="debug",
        include_detail=False,
    ),
    # 423 - Locked
    HandlerRule(
        FailedLockAcquisitionException,
        status_code=423,
        log_level="warning",
    ),
    # 500 - AWS errors (custom content builder)
    HandlerRule(
        ClientError,
        status_code=500,
        content_builder=build_client_error_content,
    ),
    # 500 - Application errors
    HandlerRule(
        ScoringEngineBaseException,
        status_code=500,
    ),
    # 500 - True catch-all (must be LAST)
    HandlerRule(
        Exception,
        status_code=500,
        log_level="critical",
        content_builder=build_custom_error_content,
    ),
]





# ──────────────────────────────────────────────────────────────────────
# 3. FastAPI Integration
# ──────────────────────────────────────────────────────────────────────
exception_handlers = create_exception_handler(handlers=HANDLER_MAP)
app = FastAPI(
    exception_handlers=exception_handlers,
)


# ──────────────────────────────────────────────────────────────────────
# 4. Custom Content Builder
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
