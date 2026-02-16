"""Cache module providing multiple cache backend implementations.

Provides InMemoryCache (sync), DatabaseCache (async), and RedisCache (async)
that all implement a common interface for consistent usage patterns.

Example usage:
    # In-memory cache (sync)
    from http_py.cache import InMemoryCache
    cache = InMemoryCache()
    cache.set("key", {"data": "value"})
    result = cache.get("key")

    # Database cache (async)
    from http_py.cache import DatabaseCache
    cache = DatabaseCache(pool)
    await cache.set("key", {"data": "value"})

    # Redis cache (async, requires `poetry add redis`)
    from http_py.cache import RedisCache
    from redis.asyncio import Redis
    client = Redis.from_url("redis://localhost:6379")
    cache = RedisCache(client)
    await cache.set("key", {"data": "value"})
"""

from http_py.cache.database_cache import DatabaseCache
from http_py.cache.in_memory_cache import (
    DEFAULT_EXPIRATION_IN_SECONDS,
    InMemoryCache,
)
from http_py.cache.models import CacheItem
from http_py.cache.protocol import AsyncCache, Cache
from http_py.cache.redis_cache import RedisCache
from http_py.cache.utils import is_cache_item_valid

__all__ = [
    # Protocols
    "AsyncCache",
    "Cache",
    # Implementations
    "DatabaseCache",
    "InMemoryCache",
    "RedisCache",
    # Models and utilities
    "CacheItem",
    "DEFAULT_EXPIRATION_IN_SECONDS",
    "is_cache_item_valid",
]
