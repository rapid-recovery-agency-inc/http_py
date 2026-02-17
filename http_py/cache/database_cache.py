"""PostgreSQL-backed cache implementation with async support."""

import json
import time
import hashlib
from typing import Any

from psycopg_pool import AsyncConnectionPool

from http_py.logging.services import create_logger


logger = create_logger(__name__)

DEFAULT_EXPIRATION_IN_SECONDS = 300  # 5 minutes


def _hash_key(key: str) -> bytes:
    """Hash a key for storage in the database.

    Uses SHA-256 for consistent, fixed-length keys.
    """
    return hashlib.sha256(key.encode("utf-8")).digest()


class DatabaseCache:
    """PostgreSQL-backed cache with TTL support.

    Uses JSONB for value storage and SHA-256 hashed keys for efficient lookups.
    Requires the cache table from 001_cache.sql migration.

    Args:
        pool: AsyncConnectionPool for database connections.
        table_name: Name of the cache table (default: "cache").
    """

    def __init__(
        self,
        pool: AsyncConnectionPool,
    ):
        self._pool = pool

    async def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache.

        Args:
            key: The cache key to look up.

        Returns:
            The cached value if found and not expired, None otherwise.
        """
        hashed_key = _hash_key(key)
        now_in_seconds = int(time.time())

        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT value, expires_at
                    FROM public.cache
                    WHERE key = %(key)s
                    LIMIT 1
                    """,
                    {"key": hashed_key},
                )
                result = await cur.fetchone()

        if result is None:
            return None

        value, expires_at = result
        if expires_at is not None and now_in_seconds >= expires_at:
            # Item is expired, remove it asynchronously
            await self.remove_item(key)
            return None

        return value

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
            raise ValueError("DatabaseCache: value cannot be None")

        hashed_key = _hash_key(key)
        now_in_seconds = int(time.time())
        expires_at = now_in_seconds + expiration_in_seconds

        # Serialize value to JSON
        json_value = json.dumps(value) if not isinstance(value, str) else value

        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO public.cache (key, plain_key, value, expires_at)
                    VALUES (%(key)s, %(plain_key)s, %(value)s, %(expires_at)s)
                    ON CONFLICT (key) DO UPDATE SET
                        value = EXCLUDED.value,
                        expires_at = EXCLUDED.expires_at,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    {
                        "key": hashed_key,
                        "plain_key": key,
                        "value": json_value,
                        "expires_at": expires_at,
                    },
                )

    async def remove_item(self, key: str) -> None:
        """Remove a specific item from the cache.

        Args:
            key: The cache key to remove.
        """
        hashed_key = _hash_key(key)

        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    DELETE FROM public.cache
                    WHERE key = %(key)s
                    """,
                    {"key": hashed_key},
                )

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache and is not expired.

        Args:
            key: The cache key to check.

        Returns:
            True if key exists and is valid, False otherwise.
        """
        hashed_key = _hash_key(key)
        now_in_seconds = int(time.time())

        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT 1
                    FROM public.cache
                    WHERE key = %(key)s
                      AND (expires_at IS NULL OR expires_at > %(now)s)
                    LIMIT 1
                    """,
                    {"key": hashed_key, "now": now_in_seconds},
                )
                result = await cur.fetchone()

        return result is not None

    async def clear(self) -> None:
        """Remove all items from the cache."""
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("TRUNCATE TABLE public.cache")

    async def cleanup_expired(self) -> int:
        """Remove all expired items from the cache.

        Returns:
            Number of items removed.
        """
        now_in_seconds = int(time.time())

        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    DELETE FROM public.cache
                    WHERE expires_at IS NOT NULL AND expires_at <= %(now)s
                    """,
                    {"now": now_in_seconds},
                )
                return cur.rowcount or 0
