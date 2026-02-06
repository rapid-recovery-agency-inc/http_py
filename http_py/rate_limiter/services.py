import asyncio

from shared.context import ServiceContext
from shared.rate_limiter.types import (
    RateLimiterRule,
    TrackRequestArgs,
    RateLimitException,
    RateLimiterRequestCount,
)
from shared.rate_limiter.utils import (
    fetch_rate_limiter_rule,
    fetch_rate_limiter_count,
    FetchDateLimiterRuleArgs,
    FetchRateLimiterCountArgs,
    save_rate_limiter_request,
    SaveRateLimiterRequestArgs,
)


async def assert_capacity(path: str, ctx: ServiceContext) -> None:
    async with asyncio.TaskGroup() as tg:
        fetch_rate_limiter_rule_args = FetchDateLimiterRuleArgs(
            ctx=ctx,
            path=path,
        )
        task1 = tg.create_task(fetch_rate_limiter_rule(fetch_rate_limiter_rule_args))
        fetch_rate_limiter_count_args = FetchRateLimiterCountArgs(
            ctx=ctx,
            path=path,
        )
        task2 = tg.create_task(fetch_rate_limiter_count(fetch_rate_limiter_count_args))

    rule: RateLimiterRule | None = task1.result()
    count: RateLimiterRequestCount | None = task2.result()

    if rule is None:
        raise RateLimitException(f"Rate limiter rule not found for: {path}")

    if count is None:
        return

    if count.monthly_count >= rule.monthly_limit:
        raise RateLimitException(f"Monthly limit exceeded for: {path} - {count}")

    if count.daily_count >= rule.daily_limit:
        raise RateLimitException(f"Daily limit exceeded for: {path} - {count}")

    if count.hourly_count >= rule.hourly_limit:
        raise RateLimitException(f"Hourly limit exceeded for: {path} - {count}")


async def track_request(args: TrackRequestArgs) -> None:
    save_args = SaveRateLimiterRequestArgs(
        ctx=args.ctx,
        path=args.path,
        request_headers=args.request_headers,
        request_body=args.request_body,
        response_headers=args.response_headers,
        response_body=args.response_body,
    )
    # INFO: Maybe we can do this in the background to reduce latency
    await save_rate_limiter_request(save_args)
