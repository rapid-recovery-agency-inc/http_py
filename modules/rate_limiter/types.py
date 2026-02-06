from typing import Self, NamedTuple

from shared.context import ServiceContext


class RateLimiterRule(NamedTuple):
    path: str
    daily_limit: int
    monthly_limit: int
    hourly_limit: int


class RateLimiterRequestCount(NamedTuple):
    path: str
    daily_count: int
    monthly_count: int
    hourly_count: int

    def __str__(self: Self) -> str:
        return (
            f"RateLimiterRequestCount(path={self.path}, "
            f"daily_count={self.daily_count}, monthly_count={self.monthly_count}, "
            f"hourly_count={self.hourly_count})"
        )


class RateLimitException(Exception):
    pass


class TrackRequestArgs(NamedTuple):
    ctx: ServiceContext
    path: str
    request_headers: str | None
    request_body: str | None
    response_headers: str | None
    response_body: str | None


class FetchDateLimiterRuleArgs(NamedTuple):
    ctx: ServiceContext
    path: str


class FetchRateLimiterCountArgs(NamedTuple):
    ctx: ServiceContext
    path: str


class SaveRateLimiterRequestArgs(NamedTuple):
    ctx: ServiceContext
    path: str
    request_headers: str | None
    request_body: str | None
    response_headers: str | None
    response_body: str | None
