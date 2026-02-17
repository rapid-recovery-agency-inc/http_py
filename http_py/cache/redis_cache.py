"""Redis-backed cache implementation with async support.

Requires the `redis` package to be installed:
    poetry add redis

Example usage:
    from redis.asyncio import Redis
    from http_py.cache.redis_cache import RedisCache

    redis_client = Redis.from_url("redis://localhost:6379")
    cache = RedisCache(redis_client)

    await cache.set("my_key", {"data": "value"})
    result = await cache.get("my_key")
"""

import json
from typing import Any, TYPE_CHECKING

from http_py.logging.services import create_logger


if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = create_logger(__name__)

DEFAULT_EXPIRATION_IN_SECONDS = 300  # 5 minutes


class RedisCache:
    """Redis-backed cache with TTL support.

    Uses Redis native TTL for expiration and JSON serialization for values.
    Supports any JSON-serializable value.

    Args:
        client: Async Redis client instance.
        prefix: Optional key prefix for namespacing (default: "cache:").
    """

    def __init__(
        self,
        client: "Redis[bytes]",
        prefix: str = "cache:",
    ):
        self._client = client
        self._prefix = prefix

    def _make_key(self, key: str) -> str:
        """Create a namespaced key."""
        return f"{self._prefix}{key}"

    async def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache.

        Args:
            key: The cache key to look up.

        Returns:
            The cached value if found, None otherwise.
            Redis handles TTL expiration automatically.
        """
        redis_key = self._make_key(key)
        value = await self._client.get(redis_key)

        if value is None:
            return None

        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # Return raw string if not valid JSON
            return value.decode("utf-8") if isinstance(value, bytes) else value

    async def set(
        self,
        key: str,
        value: Any,
        expiration_in_seconds: int = DEFAULT_EXPIRATION_IN_SECONDS,
    ) -> None:
        """Store a value in the cache with TTL.

        Args:
            key: The cache key.
            value: The value to cache (must be JSON-serializable, not None).
            expiration_in_seconds: TTL in seconds (default: 300).

        Raises:
            ValueError: If value is None.
        """
        if value is None:
            raise ValueError("RedisCache: value cannot be None")

        redis_key = self._make_key(key)

        # Serialize value to JSON
        if isinstance(value, str):
            json_value = value
        elif isinstance(value, bytes):
            json_value = value.decode("utf-8")
        else:
            json_value = json.dumps(value)

        await self._client.setex(
            name=redis_key,
            time=expiration_in_seconds,
            value=json_value,
        )

    async def remove_item(self, key: str) -> None:
        """Remove a specific item from the cache.

        Args:
            key: The cache key to remove.
        """
        redis_key = self._make_key(key)
        await self._client.delete(redis_key)

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: The cache key to check.

        Returns:
            True if key exists (and is not expired), False otherwise.
        """
        redis_key = self._make_key(key)
        return bool(await self._client.exists(redis_key))

    async def clear(self) -> None:
        """Remove all items with the configured prefix from the cache.

        Warning: This uses SCAN and may be slow on large datasets.
        Consider using a dedicated Redis database for cache if you need
        frequent clears.
        """
        pattern = f"{self._prefix}*"
        cursor = 0
        while True:
            cursor, keys = await self._client.scan(cursor=cursor, match=pattern)
            if keys:
                await self._client.delete(*keys)
            if cursor == 0:
                break

    async def get_ttl(self, key: str) -> int | None:
        """Get the remaining TTL for a key in seconds.

        Args:
            key: The cache key to check.

        Returns:
            Remaining TTL in seconds, -1 if key has no TTL, -2 if key doesn't exist.
        """
        redis_key = self._make_key(key)
        ttl = await self._client.ttl(redis_key)
        return ttl if ttl >= -2 else None

    async def set_with_nx(
        self,
        key: str,
        value: Any,
        expiration_in_seconds: int = DEFAULT_EXPIRATION_IN_SECONDS,
    ) -> bool:
        """Set a value only if the key does not exist.

        Useful for distributed locks and ensuring only one writer.

        Args:
            key: The cache key.
            value: The value to cache (must be JSON-serializable, not None).
            expiration_in_seconds: TTL in seconds (default: 300).

        Returns:
            True if the key was set, False if it already existed.

        Raises:
            ValueError: If value is None.
        """
        if value is None:
            raise ValueError("RedisCache: value cannot be None")

        redis_key = self._make_key(key)

        # Serialize value to JSON
        if isinstance(value, str):
            json_value = value
        elif isinstance(value, bytes):
            json_value = value.decode("utf-8")
        else:
            json_value = json.dumps(value)

        result = await self._client.set(
            name=redis_key,
            value=json_value,
            ex=expiration_in_seconds,
            nx=True,
        )
        return result is not None

    async def increment(self, key: str, amount: int = 1) -> int:
        """Atomically increment a counter.

        Creates the key with value 0 if it doesn't exist, then increments.

        Args:
            key: The cache key.
            amount: Amount to increment by (default: 1).

        Returns:
            The new value after incrementing.
        """
        redis_key = self._make_key(key)
        return await self._client.incrby(redis_key, amount)

    async def decrement(self, key: str, amount: int = 1) -> int:
        """Atomically decrement a counter.

        Creates the key with value 0 if it doesn't exist, then decrements.

        Args:
            key: The cache key.
            amount: Amount to decrement by (default: 1).

        Returns:
            The new value after decrementing.
        """
        redis_key = self._make_key(key)
        return await self._client.decrby(redis_key, amount)
