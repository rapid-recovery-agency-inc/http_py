"""Cache protocol defining the common interface for all cache implementations."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Cache(Protocol):
    """Protocol defining the cache interface.

    All cache implementations (InMemoryCache, DatabaseCache, RedisCache)
    must implement this interface.
    """

    def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache.

        Args:
            key: The cache key to look up.

        Returns:
            The cached value if found and not expired, None otherwise.
        """
        ...

    def set(
        self,
        key: str,
        value: Any,
        expiration_in_seconds: int = 300,
    ) -> None:
        """Store a value in the cache.

        Args:
            key: The cache key.
            value: The value to cache (must not be None).
            expiration_in_seconds: TTL in seconds (default: 300).

        Raises:
            ValueError: If value is None.
        """
        ...

    def remove_item(self, key: str) -> None:
        """Remove a specific item from the cache.

        Args:
            key: The cache key to remove.
        """
        ...

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache and is not expired.

        Args:
            key: The cache key to check.

        Returns:
            True if key exists and is valid, False otherwise.
        """
        ...

    def clear(self) -> None:
        """Remove all items from the cache."""
        ...


@runtime_checkable
class AsyncCache(Protocol):
    """Async protocol for cache implementations that support async operations.

    Use this for DatabaseCache and RedisCache which benefit from async I/O.
    """

    async def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache asynchronously."""
        ...

    async def set(
        self,
        key: str,
        value: Any,
        expiration_in_seconds: int = 300,
    ) -> None:
        """Store a value in the cache asynchronously."""
        ...

    async def remove_item(self, key: str) -> None:
        """Remove a specific item from the cache asynchronously."""
        ...

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache asynchronously."""
        ...

    async def clear(self) -> None:
        """Remove all items from the cache asynchronously."""
        ...
