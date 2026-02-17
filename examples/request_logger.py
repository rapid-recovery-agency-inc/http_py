"""Examples: http_py.request_logger module usage.

This example demonstrates request logging middleware that saves
all request/response data to a database for auditing and debugging.

Requires request_logger_request table (see migration.sql).
"""

from typing import Final

from starlette.requests import Request

from http_py.context import build_context, ServiceContext
from http_py.request_logger import create_request_logger_middleware


# ──────────────────────────────────────────────────────────────────────
# 1. Configuration
# ──────────────────────────────────────────────────────────────────────

# Paths to skip logging (health checks, static files, docs)
REQUEST_LOGGER_WHITELIST: Final[list[str]] = [
    "/health",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/favicon.ico",
]


# ──────────────────────────────────────────────────────────────────────
# 2. Create Request Logger Middleware
# ──────────────────────────────────────────────────────────────────────


async def create_service_context(request: Request) -> ServiceContext:
    """Context factory - provides database pools to middleware."""
    return await build_context(request)


# Create the middleware instance
request_logger_middleware = create_request_logger_middleware(
    path_whitelist=REQUEST_LOGGER_WHITELIST,
    create_service_context=create_service_context,
)


# ──────────────────────────────────────────────────────────────────────
# 3. FastAPI Application Setup
# ──────────────────────────────────────────────────────────────────────


def create_app_with_request_logging():
    """Create FastAPI app with request logging enabled."""
    from contextlib import asynccontextmanager

    from fastapi import FastAPI
    from starlette.middleware.base import BaseHTTPMiddleware

    from http_py.postgres import (
        cleanup_connections_pools,
        warm_up_connections_pools,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup: initialize database pools
        # await warm_up_connections_pools(env)
        yield
        # Shutdown: cleanup pools
        # await cleanup_connections_pools()

    app = FastAPI(lifespan=lifespan)

    # Add request logging middleware
    app.add_middleware(BaseHTTPMiddleware, dispatch=request_logger_middleware)

    # Example endpoints
    @app.get("/api/users")
    async def list_users():
        return {"users": [{"id": 1, "name": "Alice"}]}

    @app.post("/api/users")
    async def create_user(name: str):
        return {"id": 2, "name": name}

    @app.get("/health")
    async def health_check():
        # This endpoint is whitelisted - no logging
        return {"status": "healthy"}

    return app


# ──────────────────────────────────────────────────────────────────────
# 4. Combined with Rate Limiter
# ──────────────────────────────────────────────────────────────────────


def create_app_with_both_middlewares():
    """Create FastAPI app with both rate limiting and request logging."""
    from contextlib import asynccontextmanager

    from fastapi import FastAPI
    from starlette.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware

    from http_py.rate_limiter import create_rate_limiter_middleware
    from http_py.rate_limiter.types import RateLimitException

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield

    app = FastAPI(lifespan=lifespan)

    # Create both middlewares
    whitelist = ["/health", "/metrics", "/docs"]

    rate_limiter = create_rate_limiter_middleware(
        path_whitelist=whitelist,
        create_service_context=create_service_context,
    )
    request_logger = create_request_logger_middleware(
        path_whitelist=whitelist,
        create_service_context=create_service_context,
    )

    # Add middlewares (order matters: rate limiter first, then logger)
    # Rate limiter rejects before logging expensive requests
    app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limiter)
    app.add_middleware(BaseHTTPMiddleware, dispatch=request_logger)

    @app.exception_handler(RateLimitException)
    async def handle_rate_limit(
        request: Request, exc: RateLimitException
    ) -> JSONResponse:
        return JSONResponse(status_code=429, content={"error": str(exc)})

    @app.get("/api/data")
    async def get_data():
        return {"data": "example"}

    return app


# ──────────────────────────────────────────────────────────────────────
# 5. Database Setup (Required Table)
# ──────────────────────────────────────────────────────────────────────

# Run this SQL to create the required table (see migration.sql):
#
# CREATE TABLE request_logger_request (
#     id SERIAL PRIMARY KEY,
#     path VARCHAR(500) NOT NULL,
#     product_name VARCHAR(100),
#     product_module VARCHAR(100),
#     product_feature VARCHAR(100),
#     product_tenant VARCHAR(100),
#     from_cache BOOLEAN DEFAULT FALSE,
#     request_headers TEXT,
#     request_body TEXT,
#     response_headers TEXT,
#     response_body TEXT,
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# );
#
# -- Index for common queries
# CREATE INDEX idx_request_logger_path ON request_logger_request(path);
# CREATE INDEX idx_request_logger_created ON request_logger_request(created_at);


# ──────────────────────────────────────────────────────────────────────
# 6. Querying Logged Requests
# ──────────────────────────────────────────────────────────────────────

# Example SQL queries:
#
# -- Recent requests for a path
# SELECT * FROM request_logger_request
# WHERE path = '/api/users'
# ORDER BY created_at DESC
# LIMIT 100;
#
# -- Requests by product in last hour
# SELECT * FROM request_logger_request
# WHERE product_name = 'myapp'
# AND created_at > NOW() - INTERVAL '1 hour';
#
# -- Failed requests (no response body)
# SELECT * FROM request_logger_request
# WHERE response_body IS NULL
# ORDER BY created_at DESC;


if __name__ == "__main__":
    # Run with: poetry run python examples/request_logger.py
    import uvicorn

    app = create_app_with_request_logging()
    uvicorn.run(app, host="0.0.0.0", port=8000)
# WHERE product_name = 'myapp'
# AND created_at > NOW() - INTERVAL '1 hour';
#
# -- Failed requests (no response body)
# SELECT * FROM request_logger_request
# WHERE response_body IS NULL
# ORDER BY created_at DESC;
