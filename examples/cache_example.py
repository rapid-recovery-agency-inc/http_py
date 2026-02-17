"""Examples: http_py.cache module usage.

This example demonstrates the three cache implementations:
- InMemoryCache: Synchronous, single-process cache
- DatabaseCache: Async PostgreSQL-backed cache
- RedisCache: Async Redis-backed cache
"""

from typing import Any

from http_py.cache import (
    Cache,
    AsyncCache,
    RedisCache,
    DatabaseCache,
    InMemoryCache,
)


# ──────────────────────────────────────────────────────────────────────
# 1. InMemoryCache - Synchronous, single-process
# ──────────────────────────────────────────────────────────────────────


def in_memory_cache_example() -> None:
    """InMemoryCache: thread-safe, LRU eviction, synchronous."""
    cache = InMemoryCache(max_size=100)

    # Basic set/get
    cache.set("user:123", {"name": "Alice", "email": "alice@example.com"})
    user = cache.get("user:123")  # -> {"name": "Alice", ...}

    # Custom TTL (default is 300 seconds)
    cache.set("session:abc", {"user_id": 123}, expiration_in_seconds=60)

    # Check existence
    if cache.exists("user:123"):
        pass  # key exists and not expired

    # Remove specific item
    cache.remove_item("session:abc")

    # Get item count
    count = cache.items_count

    # Clear all items
    cache.clear()


# ──────────────────────────────────────────────────────────────────────
# 2. DatabaseCache - Async PostgreSQL-backed
# ──────────────────────────────────────────────────────────────────────


async def database_cache_example(pool: Any) -> None:
    """DatabaseCache: persistent, async, requires PostgreSQL.

    Requires running migration.sql to create the cache table.
    """
    # from http_py.postgres import get_async_writer_connection_pool
    # pool = get_async_writer_connection_pool(env)

    cache = DatabaseCache(pool, table_name="cache")  # default table: "cache"

    # Basic operations (async)
    await cache.set("key", {"data": "value"})
    result = await cache.get("key")  # -> {"data": "value"} or None
    await cache.remove_item("key")

    # Custom TTL
    await cache.set("session:123", {"user_id": 456}, expiration_in_seconds=3600)

    # Check existence
    exists = await cache.exists("session:123")

    # Cleanup expired entries (run periodically)
    deleted_count = await cache.cleanup_expired()


# ──────────────────────────────────────────────────────────────────────
# 3. RedisCache - Async Redis-backed
# ──────────────────────────────────────────────────────────────────────


async def redis_cache_example() -> None:
    """RedisCache: distributed, async, requires redis package.

    Install: poetry add redis
    """
    from redis.asyncio import Redis

    client = Redis.from_url("redis://localhost:6379")
    cache = RedisCache(client, prefix="myapp:")

    # Basic operations
    await cache.set("session:123", {"user_id": 456})
    session = await cache.get("session:123")  # -> {"user_id": 456}
    await cache.remove_item("session:123")

    # Check TTL remaining
    ttl = await cache.get_ttl("session:123")  # -> seconds or None

    # Atomic increment (useful for counters)
    count = await cache.increment("counter:visits")
    count = await cache.increment("counter:visits", amount=5)

    # Set only if not exists (useful for distributed locks)
    acquired = await cache.set_with_nx(
        "lock:job:123",
        {"worker": "abc"},
        expiration_in_seconds=30,
    )
    if acquired:
        pass  # lock acquired, do work
    else:
        pass  # another process holds the lock

    await client.aclose()


# ──────────────────────────────────────────────────────────────────────
# 4. Cache-Aside Pattern
# ──────────────────────────────────────────────────────────────────────


def cache_aside_pattern_example() -> None:
    """Cache-aside: check cache first, populate on miss."""
    cache = InMemoryCache()

    # Simulated database
    database = {
        1: {"id": 1, "name": "Alice"},
        2: {"id": 2, "name": "Bob"},
    }

    def get_user(user_id: int) -> dict | None:
        cache_key = f"user:{user_id}"

        # 1. Try cache first
        cached = cache.get(cache_key)
        if cached is not None:
            return cached  # cache hit

        # 2. Cache miss - fetch from database
        user = database.get(user_id)

        # 3. Populate cache for next time
        if user:
            cache.set(cache_key, user, expiration_in_seconds=60)

        return user

    # Usage
    user = get_user(1)  # miss -> fetches from DB, caches result
    user = get_user(1)  # hit -> returns cached value


# ──────────────────────────────────────────────────────────────────────
# 5. Using Cache Protocol for Dependency Injection
# ──────────────────────────────────────────────────────────────────────


class UserService:
    """Service that accepts any Cache implementation."""

    def __init__(self, cache: Cache) -> None:
        self._cache = cache

    def get_user(self, user_id: int) -> dict | None:
        return self._cache.get(f"user:{user_id}")

    def cache_user(self, user_id: int, data: dict) -> None:
        self._cache.set(f"user:{user_id}", data, expiration_in_seconds=300)


class AsyncUserService:
    """Service that accepts any AsyncCache implementation."""

    def __init__(self, cache: AsyncCache) -> None:
        self._cache = cache

    async def get_user(self, user_id: int) -> dict | None:
        return await self._cache.get(f"user:{user_id}")

    async def cache_user(self, user_id: int, data: dict) -> None:
        await self._cache.set(f"user:{user_id}", data, expiration_in_seconds=300)


def protocol_injection_example() -> None:
    """Use Protocol types for flexible cache backends."""
    # In-memory for development/testing
    dev_cache = InMemoryCache()
    dev_service = UserService(dev_cache)

    # For async services, use DatabaseCache or RedisCache
    # prod_cache = DatabaseCache(pool)
    # prod_service = AsyncUserService(prod_cache)
