# Rate Limiter Module

## Purpose

This module provides HTTP API rate limiting functionality as Starlette middleware. It enforces request limits at hourly, daily, and monthly intervals based on configurable rules stored in PostgreSQL.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Incoming Request                         │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              rate_limiter_middleware                        │
│  - Checks path whitelist                                    │
│  - Extracts request data (path, product_name)               │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  assert_capacity()                          │
│  - Fetches rule & count concurrently (TaskGroup)            │
│  - Compares counts against limits                           │
│  - Raises RateLimitException if exceeded                    │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌──────────────────────┬──────────────────────────────────────┐
│  fetch_rate_limiter_rule()  │  fetch_rate_limiter_count()   │
│  - Cached (5 min TTL)       │  - Cached (5 min TTL)         │
│  - Queries rate_limiter_rule│  - Aggregates hourly/daily/   │
│                             │    monthly counts             │
└──────────────────────┴──────────────────────────────────────┘
```

## File Structure

| File | Description |
|------|-------------|
| `__init__.py` | Exports `create_rate_limiter_middleware` |
| `servivces.py` | Middleware factory and core middleware logic |
| `types.py` | NamedTuples for rules/counts and `RateLimitException` |
| `utils.py` | Database queries, caching, and limit assertion logic |
| `migration.sql` | PostgreSQL schema for `rate_limiter_rule` table |

## Database Schema

### Table: `rate_limiter_rule`

Stores rate limit configurations per product and path.

| Column | Type | Description |
|--------|------|-------------|
| `id` | BIGSERIAL | Primary key |
| `product_name` | TEXT | Product identifier (from request header) |
| `path` | TEXT | API endpoint path |
| `hourly_limit` | INTEGER | Max requests per hour |
| `daily_limit` | INTEGER | Max requests per day |
| `monthly_limit` | INTEGER | Max requests per month |

### Table: `rate_limiter_request` (referenced but not in migration)

Stores individual requests for counting. Expected columns:
- `path`, `product_name`
- `hour`, `day`, `month` (encoded as integer keys, e.g., `2026020915` for hour)

## Key Types

```python
class RateLimiterRule(NamedTuple):
    path: str
    product_name: str
    daily_limit: int
    monthly_limit: int
    hourly_limit: int

class RateLimiterRequestCount(NamedTuple):
    path: str
    product_name: str
    daily_count: int
    monthly_count: int
    hourly_count: int

class RateLimitException(Exception):
    pass
```

## Usage

```python
from http_py.rate_limiter import create_rate_limiter_middleware

# Create middleware with path whitelist
middleware = create_rate_limiter_middleware(
    path_whitelist=["/health", "/metrics"],
    create_service_context=your_context_factory
)

# Add to Starlette app
app.add_middleware(BaseHTTPMiddleware, dispatch=middleware)
```

## Caching Strategy

- **In-memory cache** via `InMemoryCache` (module-level singleton)
- **TTL**: 300 seconds (5 minutes) for both rules and counts
- **Cache keys**:
  - Rules: `rule:{path}:{product_name}`
  - Counts: `count:{path}:{product_name}`

## Time Key Encoding

Counts use integer keys for efficient indexing:
- **Hour**: `YYYYMMDDHH` (e.g., `2026020915`)
- **Day**: `YYYYMMDD` (e.g., `20260209`)
- **Month**: `YYYYMM` (e.g., `202602`)

## Error Handling

- Returns HTTP 429 (Too Many Requests) when limits exceeded
- Logs `PoolTimeout` exceptions with connection pool stats
- Response includes request body and headers for debugging

## Dependencies

- `starlette` - HTTP framework
- `psycopg_pool` - PostgreSQL async connection pooling
- `http_py.context` - Request context management
- `http_py.cache.in_memory_cache` - Caching layer
- `http_py.logging` - Logging utilities

## Known Issues

1. **Typo in filename**: `servivces.py` should be `services.py`
2. **Missing migration**: `rate_limiter_request` table schema not included
3. **Bug in `fetch_rate_limiter_monthly_count`**: References `args.ctx.reader_pool` instead of `ctx.reader_pool`

## Potential Improvements

1. **Add `rate_limiter_request` migration** - Include the request tracking table schema
2. **Sliding window rate limiting** - Current implementation uses fixed time windows
3. **Redis-based counting** - For distributed deployments
4. **Configurable cache TTL** - Allow per-deployment tuning
5. **Rate limit headers** - Add `X-RateLimit-*` response headers
6. **Separate read/write concerns** - Request logging should use writer pool
7. **Graceful degradation** - Option to allow requests when rate limiter DB is unavailable
8. **Wildcard path matching** - Support patterns like `/api/v1/*`
