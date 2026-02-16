from typing import Any
from dataclasses import dataclass


@dataclass(slots=True)
class CacheItem:
    """Represents a cached item with its value and expiration timestamp.

    Attributes:
        value: The cached value.
        expires_at: Unix timestamp (seconds) when this item expires.
    """

    value: Any
    expires_at: int
