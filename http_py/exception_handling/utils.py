from typing import Any
from collections.abc import Sequence

from starlette.requests import Request

from http_py.logging.logging import create_logger
from http_py.exception_handling.types import FastAPIRequestValidationError


logger = create_logger(__name__)


# ---------------------------------------------------------------------------
# Content builders for exceptions needing custom response shapes.
# Signature: async (Request, Exception, meta) -> (content, log_extras)
# ---------------------------------------------------------------------------


async def build_validation_content(
    request: Request, exc: Exception, meta: dict[str, str]
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Capture request body and Pydantic error list for validation failures."""
    body_repr: str
    try:
        raw_body: bytes = await request.body()
        body_repr = raw_body[:2000].decode("utf-8", errors="replace")
    except (UnicodeDecodeError, RuntimeError):
        body_repr = "<unavailable>"

    validation_errors: Sequence[Any]
    if not isinstance(exc, FastAPIRequestValidationError):
        logger.error(
            f"build_validation_content: not "
            f"instance of FastAPIRequestValidationError: {exc!s}"
        )
        validation_errors = []
    else:
        validation_errors = exc.errors()
    error_count = len(validation_errors)

    content = {
        "detail": "Request validation failed",
        **meta,
        "error_count": error_count,
        "errors": validation_errors,
        "body": body_repr,
    }
    log_extras = {
        "error_count": error_count,
        "errors": validation_errors,
        "body": body_repr,
    }
    return content, log_extras


async def build_client_error_content(
    _request: Request, exc: Exception, meta: dict[str, str]
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Extract AWS metadata from ClientError response."""
    response_data = getattr(exc, "response", None)
    if not isinstance(response_data, dict):
        return {"detail": "AWS service error", **meta}, {}

    error_info = response_data.get("Error") or {}
    response_metadata = response_data.get("ResponseMetadata") or {}

    aws_meta = {
        "aws_request_id": response_metadata.get("RequestId", "unknown"),
        "http_status_code": response_metadata.get("HTTPStatusCode", 0),
        "error_code": error_info.get("Code", "UnknownError"),
        "error_message": error_info.get("Message", "No message"),
    }

    content = {"detail": "AWS service error", "aws_metadata": aws_meta, **meta}
    return content, {"aws_metadata": aws_meta}


async def build_unexpected_content(
    _request: Request, exc: Exception, meta: dict[str, str]
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Include exception type name for debugging unexpected errors."""
    exc_type = type(exc).__name__
    content = {"detail": f"Internal Server Error ({exc_type})", **meta}
    return content, {"exception_type": exc_type}
