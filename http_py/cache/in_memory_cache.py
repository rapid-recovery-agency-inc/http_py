from http_py.cache.models import CacheItem
import time
from http_py.cache.utils import is_cache_item_valid

DEFAULT_EXPIRATION_IN_SECONDS = 300  # 5 minutes


class InMemoryCache:
    def __init__(self, max_size: int = 1000):
        self.items_count = 0
        self.max_size = max_size
        self.cache: dict[str, CacheItem] = {}

    def set(
        self,
        key: str,
        value: object,
        expiration_in_seconds: int = DEFAULT_EXPIRATION_IN_SECONDS,
    ) -> None:
        if value is None:
            raise ValueError("InMemoryCache: value cannot be None")
        now_in_seconds = int(time.time())
        self.cache[key] = CacheItem(value, now_in_seconds + expiration_in_seconds)
        if self.items_count >= self.max_size:
            self._clean()
        self.items_count += 1

    def get(self, key: str) -> object | None:
        cache_item = self.cache.get(key, None)
        if cache_item is None:
            return None
        if is_cache_item_valid(cache_item):
            return cache_item.value
        self.cache.pop(key, None)
        return None

    def remove_item(self, key: str) -> None:
        self.cache.pop(key, None)

    def _clean(self) -> None:
        count = 0
        keys_to_delete = [
            key for key, value in self.cache.items() if not is_cache_item_valid(value)
        ]
        for key in keys_to_delete:
            self.cache.pop(key, None)
            count += 1
        self.items_count -= count
