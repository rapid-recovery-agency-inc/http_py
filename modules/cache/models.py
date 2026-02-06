class CacheItem:
    def __init__(self, value: object, expires_at: int = 0):
        self.expires_at = expires_at
        self.value = value
