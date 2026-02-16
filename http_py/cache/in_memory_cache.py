import time
from typing import Any

from http_py.cache.models import CacheItem
from http_py.cache.utils import is_cache_item_valid

DEFAULT_EXPIRATION_IN_SECONDS = 300  # 5 minutes


class InMemoryCache:
    """Thread-unsafe in-memory cache with TTL support.

    For thread-safe operations, use external synchronization or consider
    using a cache implementation designed for concurrent access.
    """

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: dict[str, CacheItem] = {}

    @property
    def items_count(self) -> int:
        """Return the current number of items in the cache."""
        return len(self._cache)

    def set(
        self,
        key: str,
        value: Any,
        expiration_in_seconds: int = DEFAULT_EXPIRATION_IN_SECONDS,
    ) -> None:
        """Store a value in the cache with TTL.

        Args:
            key: The cache key.
            value: The value to cache (must not be None).
            expiration_in_seconds: TTL in seconds (default: 300).

        Raises:
            ValueError: If value is None.
        """
        if value is None:
            raise ValueError("InMemoryCache: value cannot be None")

        # Clean before adding if at capacity and this is a new key
        if key not in self._cache and len(self._cache) >= self.max_size:
            self._clean()

        now_in_seconds = int(time.time())
        self._cache[key] = CacheItem(value, now_in_seconds + expiration_in_seconds)

    def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache.

        Args:
            key: The cache key to look up.

        Returns:
            The cached value if found and not expired, None otherwise.
        """
        cache_item = self._cache.get(key)
        if cache_item is None:
            return None
        if is_cache_item_valid(cache_item):
            return cache_item.value
        # Remove expired item
        self._cache.pop(key, None)
        return None

    def remove_item(self, key: str) -> None:
        """Remove a specific item from the cache.

        Args:
            key: The cache key to remove.
        """
        self._cache.pop(key, None)

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache and is not expired.

        Args:
            key: The cache key to check.

        Returns:
            True if key exists and is valid, False otherwise.
        """
        cache_item = self._cache.get(key)
        if cache_item is None:
            return False
        if is_cache_item_valid(cache_item):
            return True
        # Remove expired item
        self._cache.pop(key, None)
        return False

    def clear(self) -> None:
        """Remove all items from the cache."""
        self._cache.clear()

    def _clean(self) -> None:
        """Remove all expired items from the cache."""
        keys_to_delete = [
            key for key, item in self._cache.items() if not is_cache_item_valid(item)
        ]
        for key in keys_to_delete:
            self._cache.pop(key, None)
