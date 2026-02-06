import random
from string import Template

from psycopg_pool import ConnectionPool, AsyncConnectionPool

from modules.logging.logging import create_logger
from modules.environment.environment import env


__async_writer_cached_connection_pool: None | AsyncConnectionPool = None
__sync_writer_cached_connection_pool: None | ConnectionPool = None
__async_readers_cached_connection_pools: None | list[AsyncConnectionPool] = None

logger = create_logger(__name__)


def __get_writer_connection_string() -> str:
    """Get connection string."""
    template = Template("postgresql://$user:$password@$host:$port/$db_name")
    connection_string = template.substitute(
        user=env().DB_USERNAME,
        password=env().DB_PASSWORD,
        host=env().DB_WRITER_HOST,
        port=env().DB_PORT,
        db_name=env().DB_NAME,
    )
    return connection_string


def __get_readers_connection_strings() -> list[str]:
    """Get connection string."""
    reader_hosts = env().DB_READER_HOSTS.split(",")
    readers_connection_strings = []
    for host in reader_hosts:
        template = Template("postgresql://$user:$password@$host:$port/$db_name")
        connection_string = template.substitute(
            user=env().DB_USERNAME,
            password=env().DB_PASSWORD,
            host=host,
            port=env().DB_PORT,
            db_name=env().DB_NAME,
        )
        readers_connection_strings.append(connection_string)
    return readers_connection_strings


def get_async_writer_connection_pool() -> AsyncConnectionPool:
    """Get connection pool."""
    global __async_writer_cached_connection_pool  # noqa: PLW0603
    if __async_writer_cached_connection_pool is not None:
        return __async_writer_cached_connection_pool
    __async_writer_cached_connection_pool = AsyncConnectionPool(
        conninfo=__get_writer_connection_string(),
        timeout=env().DB_POOL_TIMEOUT,
        min_size=env().DB_MIN_POOL_SIZE,
        max_size=env().DB_MAX_POOL_SIZE,
        max_idle=env().DB_POOL_MAX_IDLE_TIME_SECONDS,
        open=False,  # https://bit.ly/3XN0fmC
    )
    return __async_writer_cached_connection_pool


def get_sync_writer_connection_pool() -> ConnectionPool:
    """Get connection pool."""
    global __sync_writer_cached_connection_pool  # noqa: PLW0603
    if __sync_writer_cached_connection_pool is not None:
        return __sync_writer_cached_connection_pool
    __sync_writer_cached_connection_pool = ConnectionPool(
        conninfo=__get_writer_connection_string(),
        timeout=env().DB_POOL_TIMEOUT,
        min_size=env().DB_MIN_POOL_SIZE,
        max_size=env().DB_MAX_POOL_SIZE,
        max_idle=env().DB_POOL_MAX_IDLE_TIME_SECONDS,
        open=False,  # https://bit.ly/3XN0fmC
    )
    return __sync_writer_cached_connection_pool


def get_async_readers_connection_pools() -> list[AsyncConnectionPool]:
    """Get connection pool."""
    global __async_readers_cached_connection_pools  # noqa: PLW0603
    if __async_readers_cached_connection_pools is not None:
        return __async_readers_cached_connection_pools
    __async_readers_cached_connection_pools = []
    for connection_string in __get_readers_connection_strings():
        pool = AsyncConnectionPool(
            conninfo=connection_string,
            timeout=env().DB_POOL_TIMEOUT,
            min_size=env().DB_MIN_POOL_SIZE,
            max_size=env().DB_MAX_POOL_SIZE,
            open=False,  # https://bit.ly/3XN0fmC
        )
        __async_readers_cached_connection_pools.append(pool)
    return __async_readers_cached_connection_pools


def get_random_reader_connection_pool() -> AsyncConnectionPool:
    """Get random reader connection pool."""
    pools = get_async_readers_connection_pools()
    return random.choice(pools)  # noqa: S311


async def warm_up_connections_pools() -> None:
    """Warm up connections pools."""
    pools = [
        get_async_writer_connection_pool(),
        *get_async_readers_connection_pools(),
        get_sync_writer_connection_pool(),
    ]
    logger.info(f"Opening connection pools: {len(pools)} pools.")
    for pool in pools:
        logger.info(f"Opening connection pool: {pool.name}")
        if isinstance(pool, ConnectionPool):
            pool.open()
            pool.wait()
        elif isinstance(pool, AsyncConnectionPool):
            await pool.open()
            await pool.wait()
        else:
            raise ValueError(f"Unknown pool type: {type(pool)}")
        pool_info = {
            "name": pool.name,
            "min_size": pool.min_size,
            "max_size": pool.max_size,
            "num_workers": pool.num_workers,
        }
        logger.info("Connection pool info: pool_info=%r", pool_info)


async def cleanup_connections_pools() -> None:
    """Cleanup connections pools."""
    global __async_writer_cached_connection_pool  # noqa: PLW0603
    global __async_readers_cached_connection_pools  # noqa: PLW0603
    if __async_writer_cached_connection_pool is not None:
        await __async_writer_cached_connection_pool.close()
        __async_writer_cached_connection_pool = None
    if __async_readers_cached_connection_pools is not None:
        for pool in __async_readers_cached_connection_pools:
            await pool.close()
        __async_readers_cached_connection_pools = None
