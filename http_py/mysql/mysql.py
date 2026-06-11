"""MySQL async connection pool management."""

from __future__ import annotations

import random

import aiomysql

from http_py.types import MySQLEnvironment
from http_py.logging.services import create_logger


__async_writer_cached_pool: aiomysql.Pool | None = None
__async_reader_cached_pools: list[aiomysql.Pool] | None = None

logger = create_logger(__name__)


def get_async_writer_connection_pool() -> aiomysql.Pool:
    """Return the cached async writer pool.

    Raises:
        RuntimeError: If ``warm_up_connections_pools`` has not been called.
    """
    if __async_writer_cached_pool is None:
        msg = (
            "MySQL writer pool is not initialised. "
            "Call warm_up_connections_pools(env) at application startup."
        )
        raise RuntimeError(msg)
    return __async_writer_cached_pool


def get_async_reader_connection_pools() -> list[aiomysql.Pool]:
    """Return the cached list of async reader pools.

    Raises:
        RuntimeError: If ``warm_up_connections_pools`` has not been called.
    """
    if __async_reader_cached_pools is None:
        msg = (
            "MySQL reader pools are not initialised. "
            "Call warm_up_connections_pools(env) at application startup."
        )
        raise RuntimeError(msg)
    return __async_reader_cached_pools


def get_random_reader_connection_pool() -> aiomysql.Pool:
    """Return a random reader pool for load balancing."""
    pools = get_async_reader_connection_pools()
    # S311: Not used for cryptography, safe to suppress
    return random.choice(pools)  # noqa: S311


async def _create_pool(
    host: str,
    env: MySQLEnvironment,
) -> aiomysql.Pool:
    """Create a single aiomysql pool for the given host."""
    pool: aiomysql.Pool = await aiomysql.create_pool(
        host=host,
        port=env.MYSQL_PORT,
        user=env.MYSQL_USERNAME,
        password=env.MYSQL_PASSWORD,
        db=env.MYSQL_DB_NAME,
        minsize=env.MYSQL_POOL_MIN_SIZE,
        maxsize=env.MYSQL_POOL_MAX_SIZE,
        connect_timeout=env.MYSQL_CONNECT_TIMEOUT,
        pool_recycle=env.MYSQL_POOL_RECYCLE,
        autocommit=False,
    )
    return pool


async def warm_up_connections_pools(env: MySQLEnvironment) -> None:
    """Create and open all MySQL connection pools.

    Must be called once at application startup before any pool accessor is used.
    """
    global __async_writer_cached_pool  # noqa: PLW0603
    global __async_reader_cached_pools  # noqa: PLW0603

    logger.info("Creating MySQL writer connection pool: host=%s", env.MYSQL_WRITER_HOST)
    __async_writer_cached_pool = await _create_pool(env.MYSQL_WRITER_HOST, env)
    logger.info(
        "MySQL writer pool ready: minsize=%d maxsize=%d",
        env.MYSQL_POOL_MIN_SIZE,
        env.MYSQL_POOL_MAX_SIZE,
    )

    reader_hosts = [h.strip() for h in env.MYSQL_READER_HOSTS.split(",") if h.strip()]
    logger.info("Creating MySQL reader connection pools: %d hosts", len(reader_hosts))
    __async_reader_cached_pools = []
    for host in reader_hosts:
        pool = await _create_pool(host, env)
        __async_reader_cached_pools.append(pool)
        logger.info("MySQL reader pool ready: host=%s", host)


async def cleanup_connections_pools() -> None:
    """Close all cached MySQL connection pools."""
    global __async_writer_cached_pool  # noqa: PLW0603
    global __async_reader_cached_pools  # noqa: PLW0603

    if __async_writer_cached_pool is not None:
        logger.info("Closing MySQL writer connection pool.")
        __async_writer_cached_pool.close()
        await __async_writer_cached_pool.wait_closed()
        __async_writer_cached_pool = None

    if __async_reader_cached_pools is not None:
        for pool in __async_reader_cached_pools:
            pool.close()
            await pool.wait_closed()
        count = len(__async_reader_cached_pools)
        logger.info("Closed %d MySQL reader connection pool(s).", count)
        __async_reader_cached_pools = None
