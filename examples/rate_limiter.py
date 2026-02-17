"""Examples: http_py.rate_limiter module usage.

This example demonstrates rate limiting middleware that enforces
hourly, daily, and monthly request limits per path/product.

Requires these database tables (see migration.sql):
- rate_limiter_rule: defines limits per path/product
- rate_limiter_count: tracks current counts
"""

from typing import Final

from starlette.requests import Request

from http_py.context import build_context, ServiceContext
from http_py.rate_limiter import create_rate_limiter_middleware
from http_py.rate_limiter.types import RateLimitException


# ──────────────────────────────────────────────────────────────────────
# 1. Configuration
# ──────────────────────────────────────────────────────────────────────

# Paths to skip rate limiting (health checks, static files, docs)
RATE_LIMIT_WHITELIST: Final[list[str]] = [
    "/health",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/favicon.ico",
]


# ──────────────────────────────────────────────────────────────────────
# 2. Create Rate Limiter Middleware
# ──────────────────────────────────────────────────────────────────────


async def create_service_context(request: Request) -> ServiceContext:
    """Context factory - provides database pools to middleware."""
    return await build_context(request)


# Create the middleware instance
rate_limiter_middleware = create_rate_limiter_middleware(
    path_whitelist=RATE_LIMIT_WHITELIST,
    create_service_context=create_service_context,
)


# ──────────────────────────────────────────────────────────────────────
# 3. FastAPI Application Setup
# ──────────────────────────────────────────────────────────────────────


def create_app_with_rate_limiting():
    """Create FastAPI app with rate limiting enabled."""
    from contextlib import asynccontextmanager

    from fastapi import FastAPI
    from starlette.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup: initialize database pools
        # await warm_up_connections_pools(env)
        yield
        # Shutdown: cleanup pools
        # await cleanup_connections_pools()

    app = FastAPI(lifespan=lifespan)

    # Add rate limiting middleware
    app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limiter_middleware)

    # Custom handler for rate limit errors (optional)
    @app.exception_handler(RateLimitException)
    async def handle_rate_limit_error(
        request: Request, exc: RateLimitException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limit_exceeded",
                "detail": str(exc),
                "path": request.url.path,
            },
        )

    # Example endpoints
    @app.get("/api/users")
    async def list_users():
        return {"users": []}

    @app.get("/health")
    async def health_check():
        # This endpoint is whitelisted - no rate limiting
        return {"status": "healthy"}

    return app


# ──────────────────────────────────────────────────────────────────────
# 4. Database Setup (Required Tables)
# ──────────────────────────────────────────────────────────────────────

# Run this SQL to create required tables (see migration.sql):
#
# CREATE TABLE rate_limiter_rule (
#     id SERIAL PRIMARY KEY,
#     path VARCHAR(500) NOT NULL,
#     product_name VARCHAR(100) NOT NULL,
#     hourly_limit INTEGER NOT NULL DEFAULT 100,
#     daily_limit INTEGER NOT NULL DEFAULT 1000,
#     monthly_limit INTEGER NOT NULL DEFAULT 10000,
#     UNIQUE(path, product_name)
# );
#
# -- Example rules:
# INSERT INTO rate_limiter_rule
#   (path, product_name, hourly_limit, daily_limit, monthly_limit)
# VALUES
#     ('/api/users', 'myapp', 100, 1000, 10000),
#     ('/api/data', 'myapp', 50, 500, 5000);


# ──────────────────────────────────────────────────────────────────────
# 5. Required Request Headers
# ──────────────────────────────────────────────────────────────────────

# Clients must send these headers for rate limiting to work:
#
# curl -X GET https://api.example.com/api/users \
#   -H "X-Product-Name: myapp" \
#   -H "X-Product-Module: users" \
#   -H "X-Product-Feature: list" \
#   -H "X-Product-Tenant: tenant-123"


if __name__ == "__main__":
    # Run with: poetry run python examples/rate_limiter.py
    import uvicorn

    app = create_app_with_rate_limiting()
    uvicorn.run(app, host="0.0.0.0", port=8000)
