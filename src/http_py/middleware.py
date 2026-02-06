"""Middleware utilities for HTTP operations."""

import logging
import time
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class CORSMiddleware:
    """CORS middleware configuration helper.

    Args:
        allow_origins: List of allowed origins or "*" for all.
        allow_methods: List of allowed HTTP methods.
        allow_headers: List of allowed headers.
        allow_credentials: Whether to allow credentials.
        max_age: Cache duration for preflight requests in seconds.
    """

    def __init__(
        self,
        allow_origins: list[str] | str = "*",
        allow_methods: list[str] | None = None,
        allow_headers: list[str] | None = None,
        allow_credentials: bool = False,
        max_age: int = 600,
    ) -> None:
        """Initialize CORSMiddleware."""
        self.allow_origins = allow_origins
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials
        self.max_age = max_age

    def get_headers(self, origin: str | None = None) -> dict[str, str]:
        """Get CORS headers for response.

        Args:
            origin: The origin from the request.

        Returns:
            Dictionary of CORS headers.
        """
        headers: dict[str, str] = {}

        # Handle allow_origins
        if isinstance(self.allow_origins, str):
            headers["Access-Control-Allow-Origin"] = self.allow_origins
        elif origin and origin in self.allow_origins:
            headers["Access-Control-Allow-Origin"] = origin
        elif self.allow_origins:
            headers["Access-Control-Allow-Origin"] = self.allow_origins[0]

        headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)

        if self.allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"

        headers["Access-Control-Max-Age"] = str(self.max_age)

        return headers


class LoggingMiddleware:
    """Logging middleware for request/response logging.

    Args:
        logger_name: Name of the logger to use.
        log_request_body: Whether to log request bodies.
        log_response_body: Whether to log response bodies.
    """

    def __init__(
        self,
        logger_name: str = "http_py",
        log_request_body: bool = False,
        log_response_body: bool = False,
    ) -> None:
        """Initialize LoggingMiddleware."""
        self.logger = logging.getLogger(logger_name)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body

    def log_request(
        self,
        method: str,
        path: str,
        headers: dict[str, str] | None = None,
        body: Any = None,
    ) -> None:
        """Log incoming request.

        Args:
            method: HTTP method.
            path: Request path.
            headers: Request headers.
            body: Request body.
        """
        log_data: dict[str, Any] = {
            "method": method,
            "path": path,
        }

        if headers:
            # Redact sensitive headers
            safe_headers = {
                k: v if k.lower() not in ["authorization", "cookie"] else "***REDACTED***"
                for k, v in headers.items()
            }
            log_data["headers"] = safe_headers

        if self.log_request_body and body is not None:
            log_data["body"] = body

        self.logger.info("Incoming request", extra=log_data)

    def log_response(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        body: Any = None,
    ) -> None:
        """Log outgoing response.

        Args:
            method: HTTP method.
            path: Request path.
            status_code: Response status code.
            duration_ms: Request duration in milliseconds.
            body: Response body.
        """
        log_data: dict[str, Any] = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
        }

        if self.log_response_body and body is not None:
            log_data["body"] = body

        level = logging.INFO if status_code < 400 else logging.WARNING
        self.logger.log(level, "Outgoing response", extra=log_data)


def timing_middleware(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to measure and log function execution time.

    Args:
        func: Function to wrap.

    Returns:
        Wrapped function.
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration_ms = (time.time() - start_time) * 1000
            logger.debug(
                f"{func.__name__} completed in {duration_ms:.2f}ms",
                extra={"function": func.__name__, "duration_ms": duration_ms},
            )

    return wrapper
