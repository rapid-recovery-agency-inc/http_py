"""Examples: http_py.logging module usage.

This example demonstrates the create_logger factory and CustomLogger class.
Set LOG_LEVEL environment variable: DEBUG, INFO, WARNING, ERROR, CRITICAL
"""

from http_py.logging import create_logger


# ──────────────────────────────────────────────────────────────────────
# 1. Basic Logging (using create_logger factory - recommended)
# ──────────────────────────────────────────────────────────────────────


def basic_logging_example() -> None:
    """Basic logging with different log levels."""
    logger = create_logger("my_service")  # Factory caches loggers by name

    # Log levels
    logger.debug("Detailed troubleshooting info")
    logger.info("General operational event")
    logger.warning("Something unexpected happened")
    logger.error("Something went wrong")
    logger.critical("System failure")


# ──────────────────────────────────────────────────────────────────────
# 2. Structured Logging with Context
# ──────────────────────────────────────────────────────────────────────


def structured_logging_example() -> None:
    """Add structured context to log messages."""
    logger = create_logger("user_service")

    # Log with user context
    logger.info(
        "User logged in",
        extra={
            "user_id": 12345,
            "email": "user@example.com",
            "action": "login",
        },
    )

    # Log with request context
    logger.info(
        "Request processed",
        extra={
            "request_id": "req-abc123",
            "method": "POST",
            "path": "/api/users",
            "client_ip": "192.168.1.100",
        },
    )


# ──────────────────────────────────────────────────────────────────────
# 3. Exception Logging
# ──────────────────────────────────────────────────────────────────────


def exception_logging_example() -> None:
    """Log exceptions with full traceback."""
    logger = create_logger("error_handler")

    try:
        result = 1 / 0
    except ZeroDivisionError:
        logger.exception("Failed to process calculation")
        # Logs message + full traceback


# ──────────────────────────────────────────────────────────────────────
# 4. Multiple Loggers for Components
# ──────────────────────────────────────────────────────────────────────


def multiple_loggers_example() -> None:
    """Separate loggers for different components - cached by name."""
    db_logger = create_logger("database")
    api_logger = create_logger("api")
    auth_logger = create_logger("authentication")

    # Same logger is returned for same name (cached)
    db_logger_again = create_logger("database")
    assert db_logger is db_logger_again

    # Each logger identifies its source in output
    db_logger.info("Connected to database")
    api_logger.info("API server started on port 8000")
    auth_logger.warning("Failed login attempt for user 'unknown'")


# ──────────────────────────────────────────────────────────────────────
# 5. FastAPI Integration
# ──────────────────────────────────────────────────────────────────────


# Example FastAPI middleware for request logging
#
# from fastapi import FastAPI, Request
# from http_py.logging import create_logger
#
# app = FastAPI()
# logger = create_logger("api")
#
# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     logger.info("Request started", extra={
#         "method": request.method,
#         "path": request.url.path,
#     })
#
#     response = await call_next(request)
#
#     logger.info("Request completed", extra={
#         "status_code": response.status_code,
#     })
#     return response


# ──────────────────────────────────────────────────────────────────────
# 6. Service Class with Logging
# ──────────────────────────────────────────────────────────────────────


class UserService:
    """Example service with integrated logging."""

    def __init__(self) -> None:
        self._logger = create_logger("user_service")

    def create_user(self, name: str, email: str) -> dict:
        self._logger.info("Creating user", extra={"name": name, "email": email})

        # ... create user logic ...
        user = {"id": 1, "name": name, "email": email}

        self._logger.info("User created", extra={"user_id": user["id"]})
        return user

    def get_user(self, user_id: int) -> dict | None:
        self._logger.debug("Fetching user", extra={"user_id": user_id})

        # ... fetch user logic ...
        user = {"id": user_id, "name": "Alice"}

        if user is None:
            self._logger.warning("User not found", extra={"user_id": user_id})
        return user
