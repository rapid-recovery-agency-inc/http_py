# Request Logger Module

## Purpose

This module provides HTTP request/response logging functionality as Starlette middleware. It captures complete request and response data and persists it to PostgreSQL for auditing, debugging, and analytics purposes.

## Recent Changes

- `__init__.py` now exports `ConsoleRequestLoggerMiddleware` and `DatabaseRequestLoggerMiddleware` directly.
- Request logging now persists `status_code`, `duration_ms`, and `request_uuid` with each record.
- The middleware always generates a `request_uuid` and exposes it to the consumer through the `RRA-Request-Logger-Request-ID` response header.
- When the middleware generates the request ID internally, the value is still returned in the response header for both successful responses and validation-error responses.
- Validation failures return `400` JSON responses without skipping request ID propagation.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Incoming Request                         │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              request_logger_middleware                      │
│  - Checks path whitelist                                    │
│  - Extracts request data (path, headers, body, product)     │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   call_next(request)                        │
│  - Executes downstream handlers                             │
│  - Captures response via StreamingResponse                  │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    save_request()                           │
│  - Persists to request_logger_request table                 │
│  - Uses writer_pool for database writes                     │
└─────────────────────────────────────────────────────────────┘
```

## File Structure

| File | Description |
|------|-------------|
| `__init__.py` | Exports `create_request_logger_middleware` |
| `services.py` | Middleware factory and core middleware logic |
| `types.py` | `RequestArgs` dataclass for passing request data |
| `utils.py` | `save_request()` database persistence function |
| `migration.sql` | PostgreSQL schema for `request_logger_request` table |

## Database Schema

### Table: `request_logger_request`

Stores complete request/response data with time-based keys for efficient querying.

| Column | Type | Description |
|--------|------|-------------|
| `id` | BIGSERIAL | Primary key |
| `created_at` | TIMESTAMP | Request timestamp |
| `path` | VARCHAR(255) | API endpoint path |
| `product_name` | TEXT | Product identifier |
| `product_module` | TEXT | Module within product |
| `product_feature` | TEXT | Feature identifier |
| `product_tenant` | TEXT | Tenant identifier |
| `month` | INTEGER | Month key (YYYYMM) |
| `day` | INTEGER | Day key (YYYYMMDD) |
| `hour` | INTEGER | Hour key (YYYYMMDDHH) |
| `from_cache` | BOOLEAN | Whether response was cached |
| `request_headers` | TEXT | Serialized request headers |
| `request_body` | TEXT | Request body content |
| `response_headers` | TEXT | Serialized response headers |
| `response_body` | TEXT | Response body content |
| `status_code` | INTEGER | HTTP response status code |
| `duration_ms` | INTEGER | End-to-end middleware duration in milliseconds |
| `request_uuid` | UUID | Correlation ID returned to the consumer and stored with the log |

### Indexes

- `request_logger_request__month_index` - (month, product_name, path)
- `request_logger_request__day_index` - (day, product_name, path)
- `request_logger_request__hour_index` - (hour, product_name, path)

## Key Types

```python
@dataclass(frozen=True)
class RequestArgs:
    ctx: Context
    path: str
    from_cache: bool
    product_name: str | None
    product_module: str | None
    product_feature: str | None
    product_tenant: str | None
    request_headers: str | None
    request_body: str | None
    response_headers: str | None
    response_body: str | None
    status_code: int | None = None
    duration_ms: int | None = None
    request_uuid: str | None = None
```

## Usage

```python
from http_py.request_logger import DatabaseRequestLoggerMiddleware
from http_py.context import create_service_context

# Add to Starlette app
app.add_middleware(
    DatabaseRequestLoggerMiddleware,
    path_whitelist=["/health", "/metrics"],
    create_service_context=create_service_context,
)
```

## Request Flow

1. **Request ID Creation**: Generates a `request_uuid` at the start of the middleware.
2. **Whitelist Check**: Requests to whitelisted paths bypass persistence, but still receive the request ID response header.
3. **Context Creation**: Creates service context from request.
4. **Data Extraction**: Extracts path, headers, body, and product metadata.
5. **Validation**: Invalid request metadata returns a `400` JSON response and still includes the request ID response header.
6. **Handler Execution**: Calls downstream request handler.
7. **Response Capture**: Consumes `StreamingResponse` body and recreates the iterator.
8. **Persistence**: Saves complete request/response data, status code, duration, and request UUID to PostgreSQL.
9. **Response Return**: Returns the response with `RRA-Request-Logger-Request-ID` exposed to the consumer.

## Response Header Contract

- `request_uuid` is always returned to the consumer in the response.
- When the service generates it, the value is exposed via the `RRA-Request-Logger-Request-ID` response header.
- This applies to both successful responses and validation-error responses.

## Product Metadata Extraction

Product fields are extracted via `extract_request_data()` from:
- **POST requests**: JSON body fields
- **GET requests**: Query parameters

Fields: `product_name`, `product_module`, `product_feature`, `product_tenant`

## Time Key Encoding

Matches the rate_limiter module for cross-querying:
- **Hour**: `YYYYMMDDHH` (e.g., `2026020915`)
- **Day**: `YYYYMMDD` (e.g., `20260209`)
- **Month**: `YYYYMM` (e.g., `202602`)

## Error Handling

- Returns `400` JSON responses when request metadata validation fails.
- Includes `RRA-Request-Logger-Request-ID` in validation-error responses.
- Logs request data even when the downstream handler raises an exception.
- Re-raises the original exception after persistence.
- Logs `PoolTimeout` exceptions from the connection pool.
- Logs an error for unexpected empty response bodies.

## Dependencies

- `starlette` - HTTP framework (StreamingResponse, iterate_in_threadpool)
- `psycopg_pool` - PostgreSQL async connection pooling
- `http_py.context` - Request context management
- `http_py.requests` - Request data extraction and validation utilities
- `http_py.logging` - Logging utilities

## Known Issues

1. **Full body capture**: May cause memory issues with large request/response bodies.
2. **Streaming limitation**: Consumes the entire response body into memory before re-streaming it.

## Potential Improvements

1. **Truncate large bodies** - Limit stored body size to prevent database bloat.
2. **Async background saving** - Decouple persistence from the request path for lower latency.
3. **Configurable field capture** - Allow disabling body/header capture per endpoint.
4. **Structured logging** - Store parsed JSON instead of raw text.
5. **Sampling options** - Log only a percentage of requests for high-traffic endpoints.
6. **Decouple from Starlette** - Abstract framework-specific code.
7. **Compression** - Compress large bodies before storage.
8. **Retention policy** - Add automated cleanup of old records.
