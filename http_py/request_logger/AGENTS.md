# Request Logger Module

## Purpose

This module provides HTTP request/response logging functionality as Starlette middleware. It captures complete request and response data and persists it to PostgreSQL for auditing, debugging, and analytics purposes.

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
    product_name: str | None
    product_module: str | None
    product_feature: str | None
    product_tenant: str | None
    request_headers: str | None
    request_body: str | None
    response_headers: str | None
    response_body: str | None
```

## Usage

```python
from http_py.request_logger import create_request_logger_middleware

# Create middleware with path whitelist
middleware = create_request_logger_middleware(
    path_whitelist=["/health", "/metrics"],
    create_service_context=your_context_factory
)

# Add to Starlette app
app.add_middleware(BaseHTTPMiddleware, dispatch=middleware)
```

## Request Flow

1. **Whitelist Check**: Requests to whitelisted paths bypass logging
2. **Context Creation**: Creates service context from request
3. **Data Extraction**: Extracts path, headers, body, and product metadata
4. **Handler Execution**: Calls downstream request handler
5. **Response Capture**: Consumes StreamingResponse body and recreates iterator
6. **Persistence**: Saves complete request/response to PostgreSQL
7. **Response Return**: Returns response to client

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

- Logs request even when downstream handler raises exception
- Re-raises original exception after logging
- Logs `PoolTimeout` exceptions from connection pool
- Logs warning for unexpected empty response bodies

## Dependencies

- `starlette` - HTTP framework (StreamingResponse, iterate_in_threadpool)
- `psycopg_pool` - PostgreSQL async connection pooling
- `http_py.context` - Request context management
- `http_py.request` - Request data extraction utilities
- `http_py.logging` - Logging utilities

## Known Issues

1. **Incorrect log message**: Error log says "rate_limiter_middleware:UnexpectedEmptyBody" but should say "request_logger_middleware"
2. **Missing status_code**: `save_request()` INSERT doesn't include `status_code` column but schema requires it as NOT NULL
3. **Full body capture**: May cause memory issues with large request/response bodies
4. **Streaming limitation**: Consumes entire response body into memory before re-streaming

## Potential Improvements

1. **Fix status_code insertion** - Add response.status_code to the INSERT statement
2. **Truncate large bodies** - Limit stored body size to prevent database bloat
3. **Async background saving** - Decouple persistence from request path for lower latency
4. **Configurable field capture** - Allow disabling body/header capture per endpoint
5. **Structured logging** - Store parsed JSON instead of raw text
6. **Sampling options** - Log only a percentage of requests for high-traffic endpoints
7. **Decouple from Starlette** - Abstract framework-specific code (noted in TODO)
8. **Add request ID tracking** - Correlate logs with trace IDs
9. **Compression** - Compress large bodies before storage
10. **Retention policy** - Add automated cleanup of old records
