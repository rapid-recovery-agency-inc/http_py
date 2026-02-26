import asyncio
from typing import cast
from datetime import UTC, datetime

from psycopg_pool import PoolTimeout

from http_py.context import ContextProtocol
from http_py.request import ExtractedRequestData
from http_py.logging.services import create_logger
from http_py.rate_limiter.types import (
    RateLimiterRule,
    RateLimitException,
    RateLimiterRequestCount,
)
from http_py.cache.in_memory_cache import InMemoryCache


CACHE = InMemoryCache()
RULE_CACHING_EXPIRATION_IN_SECONDS = 300

logger = create_logger(__name__)


async def assert_capacity(args: ExtractedRequestData, ctx: ContextProtocol) -> None:
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(fetch_rate_limiter_rule(args, ctx))
        task2 = tg.create_task(fetch_rate_limiter_count(args, ctx))

    rule: RateLimiterRule | None = task1.result()
    count: RateLimiterRequestCount | None = task2.result()

    if rule is None:
        raise RateLimitException(
            f"Rate limiter rule not found for: {args.path} - {args.product_name}"
        )

    if count is None:
        return

    if count.monthly_count >= rule.monthly_limit:
        raise RateLimitException(
            f"Monthly limit exceeded for: {args.path} - {args.product_name} - {count}"
        )

    if count.daily_count >= rule.daily_limit:
        raise RateLimitException(
            f"Daily limit exceeded for: {args.path} - {args.product_name}  - {count}"
        )

    if count.hourly_count >= rule.hourly_limit:
        raise RateLimitException(
            f"Hourly limit exceeded for: {args.path} - {args.product_name} - {count}"
        )


async def fetch_rate_limiter_rule(
    args: ExtractedRequestData, ctx: ContextProtocol
) -> RateLimiterRule | None:
    if args.path is None:
        raise ValueError("fetch_rate_limiter_rule: 'path' is required")
    if args.product_name is None:
        raise ValueError("fetch_rate_limiter_rule: 'product_name' is required")

    # Cache
    cache_key = f"rule:{args.path}:{args.product_name}"
    cached_value = CACHE.get(cache_key)
    if cached_value is not None:
        return cast(RateLimiterRule, cached_value)

    # Calculation
    async with ctx.reader.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    path,
                    product_name,
                    daily_limit,
                    monthly_limit,
                    hourly_limit
                FROM
                    rate_limiter_rule
                WHERE
                    path = %(path)s
                    AND product_name = %(product_name)s
                LIMIT
                    1
                """,
                {"path": args.path, "product_name": args.product_name},
            )
            result = await cur.fetchone()

        if not result:
            return None

        rule = RateLimiterRule(
            path=result[0],
            product_name=result[1],
            daily_limit=result[2],
            monthly_limit=result[3],
            hourly_limit=result[4],
        )
        CACHE.set(cache_key, rule, RULE_CACHING_EXPIRATION_IN_SECONDS)
        return rule


async def fetch_rate_limiter_count(
    args: ExtractedRequestData, ctx: ContextProtocol
) -> RateLimiterRequestCount | None:
    if args.path is None:
        raise ValueError("fetch_rate_limiter_count: 'path' is required")
    if args.product_name is None:
        raise ValueError("fetch_rate_limiter_count: 'product_name' is required")

    # Cache
    cache_key = f"count:{args.path}:{args.product_name}"
    cached_value = CACHE.get(cache_key)
    if cached_value is not None:
        return cast(RateLimiterRequestCount, cached_value)

    # Calculation
    # Gather the counts concurrently
    monthly_count = fetch_rate_limiter_monthly_count(args, ctx)
    daily_count = fetch_rate_limiter_daily_count(args, ctx)
    hourly_count = fetch_rate_limiter_hourly_count(args, ctx)

    result = await asyncio.gather(monthly_count, daily_count, hourly_count)
    count = RateLimiterRequestCount(
        path=args.path,
        product_name=args.product_name,
        monthly_count=result[0],
        daily_count=result[1],
        hourly_count=result[2],
    )
    CACHE.set(cache_key, count, RULE_CACHING_EXPIRATION_IN_SECONDS)
    return count


async def fetch_rate_limiter_monthly_count(
    args: ExtractedRequestData, ctx: ContextProtocol
) -> int:
    now = datetime.now(tz=UTC)
    year = now.year
    month = now.month
    month_key = (year * 100) + month
    try:
        async with ctx.reader.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM rate_limiter_request
                    WHERE
                        month = %(month_key)s
                      AND path = %(path)s
                      AND product_name = %(product_name)s
                    """,
                    {
                        "month_key": month_key,
                        "path": args.path,
                        "product_name": args.product_name,
                    },
                )
                result = await cur.fetchone()

        if result is not None:
            count = result[0]
        else:
            count = 0
        return int(count)
    except PoolTimeout as e:
        meta = {
            "stats": ctx.reader.get_stats(),
            "timeout": ctx.reader.timeout,
        }
        logger.error(
            "fetch_rate_limiter_monthly_count: PoolTimeout occurred meta=%r, "
            "exc_info=%r",
            meta,
            e,
        )
        raise e


async def fetch_rate_limiter_daily_count(
    args: ExtractedRequestData, ctx: ContextProtocol
) -> int:
    now = datetime.now(tz=UTC)
    year = now.year
    month = now.month
    day = now.day
    day_key = (((year * 100) + month) * 100) + day
    try:
        async with ctx.reader.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM rate_limiter_request
                    WHERE
                        day = %(day_key)s
                      AND path = %(path)s
                      AND product_name = %(product_name)s
                    """,
                    {
                        "day_key": day_key,
                        "path": args.path,
                        "product_name": args.product_name,
                    },
                )
                result = await cur.fetchone()

        if result is None:
            count = 0
        else:
            count = result[0]
        return int(count)
    except PoolTimeout as e:
        meta = {
            "stats": ctx.reader.get_stats(),
            "timeout": ctx.reader.timeout,
        }
        logger.error(
            "fetch_rate_limiter_daily_count: PoolTimeout occurred meta=%r, exc_info=%r",
            meta,
            e,
        )
        raise e


async def fetch_rate_limiter_hourly_count(
    args: ExtractedRequestData, ctx: ContextProtocol
) -> int:
    now = datetime.now(tz=UTC)
    year = now.year
    month = now.month
    day = now.day
    hour = now.hour
    hour_key = ((((year * 100) + month) * 100 + day) * 100) + hour
    try:
        async with ctx.reader.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM rate_limiter_request
                    WHERE
                        hour = %(hour_key)s
                      AND path = %(path)s
                        AND product_name = %(product_name)s
                    """,
                    {
                        "hour_key": hour_key,
                        "path": args.path,
                        "product_name": args.product_name,
                    },
                )
                result = await cur.fetchone()

        if result is None:
            count = 0
        else:
            count = result[0]
        return int(count)
    except PoolTimeout as e:
        meta = {
            "stats": ctx.reader.get_stats(),
            "timeout": ctx.reader.timeout,
        }
        logger.error(
            "fetch_rate_limiter_hourly_count: PoolTimeout occurred meta=%r, "
            "exc_info=%r",
            meta,
            e,
        )
        raise e
