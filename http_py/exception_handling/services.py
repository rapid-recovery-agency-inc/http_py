"""Portable factory for building unified FastAPI exception handlers.

Produces a single async handler from a declarative name→rule mapping.
Zero project-specific imports — only depends on starlette and stdlib.
"""

from typing import Any
from collections.abc import Callable, Awaitable

from starlette.requests import Request
from starlette.responses import JSONResponse

from http_py.logging.services import create_logger
from http_py.exception_handling.types import HandlerRule


logger = create_logger(__name__)


def get_request_metadata(request: Request) -> dict[str, str]:
    """Extract common request metadata for logging and responses.

    Returns dict with request_id, path, and method for use in logging
    extra dicts and response content.
    """
    return {
        "request_id": getattr(request.state, "request_id", "unknown"),
        "path": str(request.url.path),
        "method": request.method,
    }


def create_exception_handler(
    handler_map: dict[str, HandlerRule],
) -> Callable[..., Awaitable[JSONResponse]]:
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        """Unified exception handler produced by create_exception_handler."""
        meta = get_request_metadata(request)
        for rule in handler_map.values():
            if not isinstance(exc, rule.exc_type):
                continue

            # Build response content
            log_extras: dict[str, Any] = {}
            if rule.content_builder:
                content, log_extras = await rule.content_builder(request, exc, meta)
            elif rule.include_detail:
                content = {"detail": str(exc), **meta}
            else:
                content = None

            # Log (unless suppressed by DISABLED_ERROR_HANDLERS)
            if rule.log_level:
                msg = f"create_exception_handler:handler: {type(exc).__name__}"
                getattr(logger, rule.log_level)(
                    msg,
                    extra={**meta, **log_extras},
                    exc_info=(type(exc), exc, exc.__traceback__),
                )

            return JSONResponse(status_code=rule.status_code, content=content)

        # Safety net — should never reach here if catch-all Exception rule is last
        return JSONResponse(
            status_code=500,
            content={"detail": "Unhandled exception", **meta},
        )

    return handler
