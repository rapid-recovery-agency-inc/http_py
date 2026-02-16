# Cache Module

## Purpose

This module provides a unified caching abstraction with multiple backend implementations. It supports in-memory caching for single-process applications, PostgreSQL-backed caching for persistent shared cache, and Redis caching for distributed high-performance scenarios.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Code                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Cache / AsyncCache Protocol                    │
│  - get(key) → value | None                                  │
│  - set(key, value, ttl)                                     │
│  - remove_item(key)                                         │
│  - exists(key) → bool                                       │
│  - clear()                                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌───────────────┬───────────────┬───────────────┐
│ InMemoryCache │ DatabaseCache │  RedisCache   │
│    (sync)     │   (async)     │   (async)     │
│               │               │               │
│ - dict-based  │ - PostgreSQL  │ - Redis       │
│ - TTL check   │ - JSONB       │ - Native TTL  │
│ - Max size    │ - SHA-256 key │ - Namespacing │
│ - Auto-clean  │ - Upsert      │ - Atomic ops  │
└───────────────┴───────────────┴───────────────┘
```

## File Structure

| File | Description |
|------|-------------|
| `__init__.py` | Exports public API: protocols, implementations, utilities |
| `protocol.py` | `Cache` and `AsyncCache` protocols defining the interface |
| `in_memory_cache.py` | Synchronous in-memory cache with TTL and max size |
| `database_cache.py` | Async PostgreSQL-backed cache with JSONB storage |
| `redis_cache.py` | Async Redis-backed cache with native TTL and atomic operations |
| `models.py` | `CacheItem` dataclass for internal representation |
| `utils.py` | Utility functions like `is_cache_item_valid()` |
| `migration.sql` | PostgreSQL schema for `cache` table |

## Implementations

### InMemoryCache (Synchronous)

Best for: Single-process applications, development, testing, short-lived caches.

```python
from http_py.cache import InMemoryCache

cache = InMemoryCache(max_size=1000)
cache.set("user:123", {"name": "Alice"}, expiration_in_seconds=300)
user = cache.get("user:123")
```

**Features:**
- Dictionary-based storage
- Automatic cleanup when max size reached
- Lazy expiration (checked on access)
- Thread-unsafe (use external locking for concurrent access)

### DatabaseCache (Async)

Best for: Persistent cache, shared across multiple processes, moderate throughput.

```python
from http_py.cache import DatabaseCache
from http_py.postgres.postgres import get_async_writer_connection_pool

pool = get_async_writer_connection_pool()
cache = DatabaseCache(pool)

await cache.set("config:app", {"debug": True})
config = await cache.get("config:app")
```

**Features:**
- PostgreSQL with JSONB storage
- SHA-256 hashed keys for consistent key length
- Upsert semantics (INSERT ... ON CONFLICT)
- `cleanup_expired()` method for batch cleanup
- Survives process restarts

### RedisCache (Async)

Best for: Distributed cache, high throughput, atomic operations, pub/sub patterns.

```python
from redis.asyncio import Redis
from http_py.cache import RedisCache

client = Redis.from_url("redis://localhost:6379")
cache = RedisCache(client, prefix="myapp:")

await cache.set("session:abc", {"user_id": 123})
session = await cache.get("session:abc")
```

**Features:**
- Native Redis TTL (automatic expiration)
- Key namespacing with configurable prefix
- Atomic operations: `increment()`, `decrement()`, `set_with_nx()`
- `get_ttl()` for remaining TTL inspection
- JSON serialization for complex values

## Database Schema

### Table: `cache`

| Column | Type | Description |
|--------|------|-------------|
| `id` | BIGSERIAL | Primary key |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |
| `key` | BYTEA | SHA-256 hash of the key (unique) |
| `plain_key` | TEXT | Original key for debugging |
| `value` | JSONB | Cached value |
| `expires_at` | BIGINT | Unix timestamp, NULL = never expires |

**Indexes:**
- `cache_key_hash_idx` - HASH index on `key` for O(1) lookups
- `cache_expires_at_idx` - Partial index on `expires_at` for cleanup queries

## Protocols

### Cache (Synchronous)

```python
class Cache(Protocol):
    def get(self, key: str) -> Any | None: ...
    def set(self, key: str, value: Any, expiration_in_seconds: int = 300) -> None: ...
    def remove_item(self, key: str) -> None: ...
    def exists(self, key: str) -> bool: ...
    def clear(self) -> None: ...
```

### AsyncCache (Asynchronous)

```python
class AsyncCache(Protocol):
    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, expiration_in_seconds: int = 300) -> None: ...
    async def remove_item(self, key: str) -> None: ...
    async def exists(self, key: str) -> bool: ...
    async def clear(self) -> None: ...
```

## Usage Patterns

### Cache-Aside Pattern

```python
async def get_user(user_id: int, cache: AsyncCache, db: Database) -> User:
    cache_key = f"user:{user_id}"
    
    # Try cache first
    cached = await cache.get(cache_key)
    if cached is not None:
        return User(**cached)
    
    # Fetch from database
    user = await db.fetch_user(user_id)
    
    # Store in cache
    await cache.set(cache_key, user.dict(), expiration_in_seconds=600)
    
    return user
```

### Distributed Lock with RedisCache

```python
async def process_with_lock(job_id: str, cache: RedisCache) -> bool:
    lock_key = f"lock:{job_id}"
    
    # Try to acquire lock
    acquired = await cache.set_with_nx(lock_key, "locked", expiration_in_seconds=30)
    if not acquired:
        return False  # Another process has the lock
    
    try:
        await do_work(job_id)
        return True
    finally:
        await cache.remove_item(lock_key)
```

### Rate Limiting Counter

```python
async def check_rate_limit(user_id: int, cache: RedisCache, limit: int = 100) -> bool:
    key = f"ratelimit:{user_id}:{current_minute()}"
    count = await cache.increment(key)
    
    if count == 1:
        # First request this minute, set TTL
        await cache._client.expire(cache._make_key(key), 60)
    
    return count <= limit
```

## Design Principles

1. **Protocol-Based Interface**: All implementations conform to `Cache` or `AsyncCache` protocols for interchangeability
2. **TTL First**: All implementations support time-based expiration out of the box
3. **None-Safety**: Setting `None` values is explicitly disallowed to distinguish "not found" from "cached null"
4. **Lazy Expiration**: In-memory and database caches check expiration on access; Redis uses native TTL
5. **JSON Serialization**: Complex values are JSON-encoded for cross-process compatibility

## Future Enhancements

### Planned Features

- [ ] **Multi-Level Cache**: L1 (in-memory) + L2 (Redis/Database) with automatic promotion
- [ ] **Cache Stampede Prevention**: Probabilistic early expiration or locking
- [ ] **Batch Operations**: `mget()`, `mset()` for multiple keys in one round-trip
- [ ] **Cache Statistics**: Hit/miss ratios, latency tracking, size monitoring
- [ ] **Serialization Options**: MessagePack, Pickle, custom serializers
- [ ] **Cache Tags**: Group related keys for batch invalidation
- [ ] **Write-Through/Write-Behind**: Automatic database synchronization
- [ ] **Circuit Breaker**: Graceful degradation when cache backend is unavailable
- [ ] **Compression**: Optional gzip/lz4 for large values

### Extension Points

1. **Custom Serializers**: Implement custom encode/decode for specific value types
2. **Key Transformers**: Namespace, hash, or transform keys before storage
3. **Event Hooks**: on_hit, on_miss, on_set, on_evict callbacks
4. **Metrics Integration**: Prometheus, StatsD, OpenTelemetry exporters

### Migration Notes

When adding a new cache backend:
1. Implement `Cache` (sync) or `AsyncCache` (async) protocol
2. Support `get`, `set`, `remove_item`, `exists`, `clear` methods
3. Handle TTL expiration (native or application-level)
4. Reject `None` values with `ValueError`
5. Add to `__init__.py` exports
6. Document backend-specific features in this file
