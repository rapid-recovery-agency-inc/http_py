# http_py

## Purpose

Shared HTTP and service utilities for Python microservices. The package is organized by cross-cutting capability rather than by application.

## Strategic Map

- `http_py/environment` - typed environment loading and validation. See [http_py/environment/AGENTS.md](http_py/environment/AGENTS.md).
- `http_py/exceptions` - reusable exception response and mapping helpers. See [http_py/exceptions/AGENTS.md](http_py/exceptions/AGENTS.md).
- `http_py/logging` - structured logging primitives. See [http_py/logging/AGENTS.md](http_py/logging/AGENTS.md).
- `http_py/postgres` - default database backing via psycopg writer and reader pools. See [http_py/postgres/AGENTS.md](http_py/postgres/AGENTS.md).
- `http_py/sqla` - opt-in SQLAlchemy adapters and context helpers. See [http_py/sqla/AGENTS.md](http_py/sqla/AGENTS.md).
- `http_py/request_logger` - request capture and persistence middleware. See [http_py/request_logger/AGENTS.md](http_py/request_logger/AGENTS.md).
- `http_py/rate_limiter` - request throttling middleware and SQL helpers. See [http_py/rate_limiter/AGENTS.md](http_py/rate_limiter/AGENTS.md).
- `http_py/cache` - in-memory, database, and Redis cache implementations. See [http_py/cache/AGENTS.md](http_py/cache/AGENTS.md).
- `http_py/e2e_testing` - isolated database-backed test helpers. See [http_py/e2e_testing/AGENTS.md](http_py/e2e_testing/AGENTS.md).
- `http_py/hmac` - HMAC verification helpers. See [http_py/hmac/AGENTS.md](http_py/hmac/AGENTS.md).

## Database Direction

The default database integration path is psycopg connection pools from `http_py.postgres`.

`http_py` also supports SQLAlchemy-backed usage through the adapter and context helpers in `http_py.sqla`. SQLAlchemy support is opt-in and does not change the default psycopg API.

## Testing

Keep tests close to the module they verify. Follow the existing local `unittest` style unless the module already establishes a different testing pattern.