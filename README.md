# http_py

A Python library providing common utilities and patterns for building microservices and HTTP APIs with FastAPI and other Python web frameworks.

## Installation

```bash
poetry add http_py
```

## Modules

### 🌍 Environment Management

Type-safe environment variable loading with validation and coercion.

```python
from dataclasses import dataclass
from http_py.environment import create_environment

# ──────────────────────────────────────────────────────────────────────
# 1. Custom converter via field metadata
# ──────────────────────────────────────────────────────────────────────
#
# Any field that needs non-standard coercion can declare a converter
# in its ``metadata`` dict.  The converter receives the raw value and
# must return the coerced result.

BooleanString = Literal["true", "false"]


def to_boolean_string(value: bool | int | str) -> BooleanString:
    """Convert various truthy/falsy representations to "true"/"false"."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return "true" if value == 1 else "false"
    return "true" if str(value).lower() == "true" else "false"


@dataclass(frozen=True)
class AppEnvironment:
    """A sample frozen dataclass defining the environment shape."""

    DEBUG: bool = False
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "mydb"
    FEATURE_FLAG: BooleanString = field(
        default="false",
        metadata={"converter": to_boolean_string},
    )


# ──────────────────────────────────────────────────────────────────────
# 2. Bootstrap — call create_environment once
# ──────────────────────────────────────────────────────────────────────

_manager = create_environment(AppEnvironment)
env = _manager.env
set_environment = _manager.set_environment
```

**Features:**
- Frozen dataclass-based configuration
- Automatic type coercion (str → bool, int, float, list, dict)
- Required vs optional field validation
- Custom validators support

📖 [Environment Example](examples/environment_example.py)

---

### 🗄️ Caching

Multiple cache implementations with a unified Protocol interface.

```python
from http_py.cache import InMemoryCache, DatabaseCache, RedisCache

# In-memory (synchronous, single process)
cache = InMemoryCache(max_size=1000)
cache.set("key", {"data": "value"}, expiration_in_seconds=300)
result = cache.get("key")

# Database-backed (async, PostgreSQL)
db_cache = DatabaseCache(pool)
await db_cache.set("key", data)

# Redis-backed (async, distributed)
redis_cache = RedisCache(redis_client)
await redis_cache.set("key", data)
```

📖 [Cache Example](examples/cache_example.py)

---

### ⚠️ Exception Handling

Declarative exception handler factory for consistent error responses.

```python
from http_py.exception_handling import ExceptionHandlerFactory, ExceptionDeclaration

# Define exception mappings
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
   ...
}

def create_app() -> FastAPI:
    """Create FastAPI app with unified exception handler."""
    app = FastAPI()

    # Create single handler for all exceptions
    exception_handler = create_exception_handler(handler_map=HANDLER_MAP)

    # Register for validation errors and all exceptions
    app.add_exception_handler(RequestValidationError, exception_handler)
    app.add_exception_handler(Exception, exception_handler)

    return app
```

📖 [Exception Handling Example](examples/exception_handling_example.py)

---

### 🐘 PostgreSQL

Connection pool management with writer/reader separation.

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from http_py.postgres import (
    get_async_writer_connection_pool,
    get_random_reader_connection_pool,
    warm_up_connections_pools,
    cleanup_connections_pools,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - warm up connection pools
    await warm_up_connections_pools(env)
    yield
    # Shutdown - close all pools
    await cleanup_connections_pools()

app = FastAPI(lifespan=lifespan)

@app.get("/users/{user_id}")
async def get_user_endpoint(user_id: int):
    pool = get_random_reader_connection_pool(env)  # Uses read replica
    user = await get_user(pool, user_id)
    if user:
        return user
    return {"error": "User not found"}

@app.post("/users")
async def create_user_endpoint(name: str, email: str):
    pool = get_async_writer_connection_pool(env)  # Uses primary
    user_id = await create_user(pool, name, email)
    return {"id": user_id}
```

📖 [PostgreSQL Example](examples/postgres_example.py)

---

### 📝 Logging

Structured logging with context support.

```python
from http_py.logging import create_logger

logger = create_logger(__name__)

logger.info("User logged in", extra={
    "user_id": 123,
    "method": "oauth",
})

logger.error("Failed to process", extra={
    "error_code": "E001",
    "request_id": "abc123",
})
```

📖 [Logging Example](examples/logging_example.py)

---

### 🔐 HMAC

HMAC-SHA256 signature verification for webhooks and secure APIs.

```python
from fastapi import FastAPI, Request, Depends
from http_py.hmac import require_hmac_signature, HMACException

app = FastAPI()

env = HMACEnv(
    SECRETS=["current_secret", "previous_secret"],  # Key rotation
    HMAC_HEADER_NAME="X-HMAC-Signature",
)

async def verify_hmac(request: Request):
    '''Dependency to verify HMAC signature.'''
    await require_hmac_signature(request, env)

@app.post("/secure/endpoint", dependencies=[Depends(verify_hmac)])
async def secure_endpoint():
    return {"status": "authorized"}

@app.exception_handler(HMACException)
async def handle_hmac_error(request: Request, exc: HMACException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )
```

📖 [HMAC Example](examples/hmac_example.py)

---

### 🚦 Rate Limiting

Rate limiting middleware with Redis support.

```python
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
```

📖 [Rate Limiter Example](examples/rate_limiter_example.py)

---

### 📊 Request Logger

Request/response logging middleware for observability.

```python
    from contextlib import asynccontextmanager

    from fastapi import FastAPI
    from starlette.middleware.base import BaseHTTPMiddleware

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
```

📖 [Request Logger Example](examples/request_logger_example.py)

---

### 🧪 E2E Testing

End-to-end testing utilities with isolated database per test.

```python
from http_py.e2e_testing import CustomAsyncTestCase

class TestUserService(CustomAsyncTestCase):
    migrations_folder_path = "migrations"

    async def test_create_user(self):
        async with self.pool.connection() as conn:
            await conn.execute(
                "INSERT INTO users (name) VALUES (%s)",
                ("Alice",)
            )
            # Test runs in isolated database
            # Database is dropped after test
```

📖 [E2E Testing Example](examples/e2e_testing_example.py)

---

## Development

```bash
# Install dependencies
poetry install

# Format code
poetry run ruff format .

# Lint
poetry run ruff check --fix .

# Type check
poetry run mypy http_py --ignore-missing-imports

# Run all checks
poetry run pre-commit run --all-files
```

## Requirements

- Python 3.13+
- PostgreSQL (for database features)
- Redis (optional, for distributed caching/rate limiting)

## License

MIT