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
from http_py.environment import EnvironmentFactory

@dataclass(frozen=True)
class Env:
    DATABASE_URL: str
    DEBUG: bool = False
    MAX_CONNECTIONS: int = 10

factory = EnvironmentFactory()
env = factory.create(Env)  # Loads from os.environ with validation
```

**Features:**
- Frozen dataclass-based configuration
- Automatic type coercion (str → bool, int, float, list, dict)
- Required vs optional field validation
- Custom validators support

📖 [Environment Example](examples/environment.py)

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

📖 [Cache Example](examples/cache.py)

---

### ⚠️ Exception Handling

Declarative exception handler factory for consistent error responses.

```python
from http_py.exception_handling import ExceptionHandlerFactory, ExceptionDeclaration

# Define exception mappings
declarations = [
    ExceptionDeclaration(ValueError, 400, "VALIDATION_ERROR"),
    ExceptionDeclaration(PermissionError, 403, "FORBIDDEN"),
    ExceptionDeclaration(FileNotFoundError, 404, "NOT_FOUND"),
]

factory = ExceptionHandlerFactory(declarations)
handler = factory.create_handler()

# Add to FastAPI
app.add_exception_handler(Exception, handler)
```

📖 [Exception Handling Example](examples/exception_handling.py)

---

### 🐘 PostgreSQL

Connection pool management with writer/reader separation.

```python
from http_py.postgres import (
    init_async_postgres_pool,
    get_async_writer_connection_pool,
    get_async_reader_connection_pool,
    close_async_postgres_pools,
)

# Initialize on startup
init_async_postgres_pool(env)

# Use writer for mutations
writer_pool = get_async_writer_connection_pool(env)
async with writer_pool.connection() as conn:
    await conn.execute("INSERT INTO users ...")

# Use reader for queries (uses read replica if configured)
reader_pool = get_async_reader_connection_pool(env)
async with reader_pool.connection() as conn:
    result = await conn.execute("SELECT * FROM users")
```

📖 [PostgreSQL Example](examples/postgres_example.py)

---

### 📝 Logging

Structured logging with context support.

```python
from http_py.logging import CustomLogger

logger = CustomLogger("my_service")

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
from http_py.hmac import hmac_validator

validator = hmac_validator()

# Verify webhook signature
is_valid = validator.verify_signature(
    signature=request.headers["X-Signature"],
    payload=await request.body(),
    secret=env.SECRETS["webhook_provider"]
)
```

📖 [HMAC Example](examples/hmac_example.py)

---

### 🚦 Rate Limiting

Rate limiting middleware with Redis support.

```python
from http_py.rate_limiter import RateLimiter, RateLimitConfig

config = RateLimitConfig(
    requests_per_window=100,
    window_seconds=60
)

rate_limiter = RateLimiter(config)

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if not await rate_limiter.check(request.client.host):
        return JSONResponse(status_code=429, content={"error": "Too many requests"})
    return await call_next(request)
```

📖 [Rate Limiter Example](examples/rate_limiter.py)

---

### 📊 Request Logger

Request/response logging middleware for observability.

```python
from http_py.request_logger import request_logger_middleware

app.add_middleware(request_logger_middleware)

# Logs: method, path, status_code, duration, client_ip
```

📖 [Request Logger Example](examples/request_logger.py)

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

📖 [E2E Testing Example](examples/e2e_testing.py)

---

## Additional Utilities

### Context Management

```python
from http_py.context import build_context

# Build application context with all services
context = build_context(env)
```

### Request Helpers

```python
from http_py.request import get_raw_body

# Get raw request body (useful for signature verification)
body = await get_raw_body(request)
```

### Shortcuts

```python
from http_py.shortcuts import ok, created, no_content, bad_request

# Quick response builders
return ok({"data": result})
return created({"id": new_id})
return bad_request("Invalid input")
```

### Validators

```python
from http_py.validators import validate_email, validate_url

# Input validation
is_valid = validate_email("user@example.com")
```

### AWS Integration

```python
from http_py.aws import get_secrets_from_aws

# Load secrets from AWS Secrets Manager
secrets = get_secrets_from_aws(secret_name="my-app/prod")
```

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

- Python 3.11+
- PostgreSQL (for database features)
- Redis (optional, for distributed caching/rate limiting)

## License

MIT