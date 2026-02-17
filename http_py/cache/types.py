"""Type definitions for cache module."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AsyncRedisClient(Protocol):
    """Protocol defining the async Redis client interface used by RedisCache.

    This allows using any Redis-compatible async client without depending
    on the redis package directly.
    """

    async def get(self, name: str) -> bytes | None:
        """Get the value of a key."""
        ...

    async def setex(
        self,
        name: str,
        time: int,
        value: str | bytes,
    ) -> Any:
        """Set key to value with expiration time in seconds."""
        ...

    async def set(
        self,
        name: str,
        value: str | bytes,
        ex: int | None = None,
        nx: bool = False,
    ) -> Any | None:
        """Set key to value with optional expiration and NX flag."""
        ...

    async def delete(self, *names: str | bytes) -> int:
        """Delete one or more keys."""
        ...

    async def exists(self, *names: str) -> int:
        """Return the number of keys that exist."""
        ...

    async def scan(
        self,
        cursor: int = 0,
        match: str | None = None,
        count: int | None = None,
    ) -> tuple[int, list[bytes]]:
        """Scan keys matching a pattern."""
        ...

    async def incrby(self, name: str, amount: int = 1) -> int:
        """Increment the value of key by amount."""
        ...

    async def decrby(self, name: str, amount: int = 1) -> int:
        """Decrement the value of key by amount."""
        ...
