from typing import Self, NamedTuple


class RateLimiterRule(NamedTuple):
    path: str
    product_name: str
    daily_limit: int
    monthly_limit: int
    hourly_limit: int


class RateLimiterRequestCount(NamedTuple):
    path: str
    product_name: str
    daily_count: int
    monthly_count: int
    hourly_count: int

    def __str__(self: Self) -> str:
        return (
            f"RateLimiterRequestCount(path={self.path}, product_name={self.product_name}, "
            f"daily_count={self.daily_count}, monthly_count={self.monthly_count}, "
            f"hourly_count={self.hourly_count})"
        )


class RateLimitException(Exception):
    pass
