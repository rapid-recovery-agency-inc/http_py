import time
from http_py.cache.models import CacheItem


def is_cache_item_valid(cache_item: CacheItem) -> bool:
    if cache_item is None:
        return False
    if cache_item.expires_at is None or cache_item.value is None:
        return False
    now_in_seconds = int(time.time())
    return now_in_seconds < cache_item.expires_at
