import asyncio
from typing import cast
from datetime import UTC, datetime

from psycopg_pool import PoolTimeout

from modules.logging.logging import create_logger
from modules.cache.in_memory_cache import InMemoryCache
from shared.rate_limiter.types import (
    RateLimiterRule,
    RateLimiterRequestCount,
    FetchDateLimiterRuleArgs,
    FetchRateLimiterCountArgs,
    SaveRateLimiterRequestArgs,
)


CACHE = InMemoryCache()
RULE_CACHING_EXPIRATION_IN_SECONDS = 300

logger = create_logger(__name__)


async def fetch_rate_limiter_rule(
    args: FetchDateLimiterRuleArgs,
) -> RateLimiterRule | None:
    if args.path is None:
        raise ValueError("fetch_rate_limiter_rule: 'path' is required")

    # Cache
    cache_key = f"rule:{args.path}"
    cached_value = CACHE.get(cache_key)
    if cached_value is not None:
        return cast(RateLimiterRule, cached_value)

    # Calculation
    async with args.ctx.reader_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT path,
                       daily_limit,
                       monthly_limit,
                       hourly_limit
                FROM rate_limiter_rule
                WHERE path = %(path)s LIMIT
                    1
                """,
                {"path": args.path},
            )
            result = await cur.fetchone()

        if not result:
            return None

        rule = RateLimiterRule(
            path=result[0],
            daily_limit=result[1],
            monthly_limit=result[2],
            hourly_limit=result[3],
        )
        CACHE.set(cache_key, rule, RULE_CACHING_EXPIRATION_IN_SECONDS)
        return rule


async def fetch_rate_limiter_count(
    args: FetchRateLimiterCountArgs,
) -> RateLimiterRequestCount | None:
    if args.path is None:
        raise ValueError("fetch_rate_limiter_count: 'path' is required")

    # Cache
    cache_key = f"count:{args.path}"
    cached_value = CACHE.get(cache_key)
    if cached_value is not None:
        return cast(RateLimiterRequestCount, cached_value)

    # Calculation
    # Gather the counts concurrently
    monthly_count = fetch_rate_limiter_monthly_count(args)
    daily_count = fetch_rate_limiter_daily_count(args)
    hourly_count = fetch_rate_limiter_hourly_count(args)

    result = await asyncio.gather(monthly_count, daily_count, hourly_count)
    count = RateLimiterRequestCount(
        path=args.path,
        monthly_count=result[0],
        daily_count=result[1],
        hourly_count=result[2],
    )
    CACHE.set(cache_key, count, RULE_CACHING_EXPIRATION_IN_SECONDS)
    return count


async def fetch_rate_limiter_monthly_count(args: FetchRateLimiterCountArgs) -> int:
    if args.path is None:
        raise ValueError("fetch_rate_limiter_monthly_count: 'path' is required")

    # Calculation
    now = datetime.now(tz=UTC)
    year = now.year
    month = now.month
    month_key = (year * 100) + month
    try:
        async with args.ctx.reader_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM rate_limiter_request
                    WHERE
                        month = %(month_key)s
                      AND path = %(path)s
                    """,
                    {"month_key": month_key, "path": args.path},
                )
                result = await cur.fetchone()

        if result is not None:
            count = result[0]
        else:
            count = 0
        return int(count)
    except PoolTimeout as e:
        meta = {
            "stats": args.ctx.reader_pool.get_stats(),
            "timeout": args.ctx.reader_pool.timeout,
        }
        logger.error(
            "fetch_rate_limiter_monthly_count: PoolTimeout occurred meta=%r, "
            "exc_info=%r",
            meta,
            e,
        )
        raise e


async def fetch_rate_limiter_daily_count(args: FetchRateLimiterCountArgs) -> int:
    if args.path is None:
        raise ValueError("fetch_rate_limiter_daily_count: 'path' is required")

    # Calculation
    now = datetime.now(tz=UTC)
    year = now.year
    month = now.month
    day = now.day
    day_key = (((year * 100) + month) * 100) + day
    try:
        async with args.ctx.reader_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM rate_limiter_request
                    WHERE
                        day = %(day_key)s
                      AND path = %(path)s
                    """,
                    {"day_key": day_key, "path": args.path},
                )
                result = await cur.fetchone()

        if result is None:
            count = 0
        else:
            count = result[0]
        return int(count)
    except PoolTimeout as e:
        meta = {
            "stats": args.ctx.reader_pool.get_stats(),
            "timeout": args.ctx.reader_pool.timeout,
        }
        logger.error(
            "fetch_rate_limiter_daily_count: PoolTimeout occurred meta=%r, exc_info=%r",
            meta,
            e,
        )
        raise e


async def fetch_rate_limiter_hourly_count(args: FetchRateLimiterCountArgs) -> int:
    if args.path is None:
        raise ValueError("fetch_rate_limiter_hourly_count: 'path' is required")

    # Calculation
    now = datetime.now(tz=UTC)
    year = now.year
    month = now.month
    day = now.day
    hour = now.hour
    hour_key = ((((year * 100) + month) * 100 + day) * 100) + hour
    try:
        async with args.ctx.reader_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM rate_limiter_request
                    WHERE
                        hour = %(hour_key)s
                      AND path = %(path)s
                    """,
                    {"hour_key": hour_key, "path": args.path},
                )
                result = await cur.fetchone()

        if result is None:
            count = 0
        else:
            count = result[0]
        return int(count)
    except PoolTimeout as e:
        meta = {
            "stats": args.ctx.reader_pool.get_stats(),
            "timeout": args.ctx.reader_pool.timeout,
        }
        logger.error(
            "fetch_rate_limiter_hourly_count: PoolTimeout occurred meta=%r, "
            "exc_info=%r",
            meta,
            e,
        )
        raise e


async def save_rate_limiter_request(args: SaveRateLimiterRequestArgs) -> None:
    if any(
        v is None
        for v in [
            args.path,
        ]
    ):
        raise ValueError("save_rate_limiter_request: 'path' is  required")

    try:
        async with args.ctx.writer_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO rate_limiter_request
                    (path, request_headers, request_body, response_headers,
                     response_body)
                    VALUES (%(path)s, %(request_headers)s, %(request_body)s,
                            %(response_headers)s, %(response_body)s)
                    """,
                    {
                        "path": args.path,
                        "request_headers": args.request_headers,
                        "request_body": args.request_body,
                        "response_headers": args.response_headers,
                        "response_body": args.response_body,
                    },
                )
    except PoolTimeout as e:
        logger.exception("save_rate_limiter_request: PoolTimeout occurred", exc_info=e)
        raise e
