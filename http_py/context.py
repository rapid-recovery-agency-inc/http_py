import random
from typing import Protocol
from collections.abc import Callable, Awaitable

from psycopg_pool import AsyncConnectionPool

from http_py.types import PostgressEnvironment
from http_py.request import Request
from http_py.postgres import (
    get_async_writer_connection_pool,
    get_random_reader_connection_pool,
)


class Context(Protocol):
    writer_pool: AsyncConnectionPool
    reader_pools: list[AsyncConnectionPool]

    @property
    def writer(self) -> AsyncConnectionPool:
        return self.writer_pool

    @property
    def reader(self) -> AsyncConnectionPool:
        return random.choice(self.reader_pools)  # noqa: S311


ContextFactory = Callable[[Request], Awaitable[Context]]


class ServiceContext:
    # @deprecated: user `writer_pool` instead
    pool: AsyncConnectionPool
    writer_pool: AsyncConnectionPool
    reader_pool: AsyncConnectionPool

    def __init__(
        self,
        writer_pool: AsyncConnectionPool,
        reader_pool: AsyncConnectionPool,
    ):
        self.pool = reader_pool
        self.reader_pool = reader_pool
        self.writer_pool = writer_pool


async def build_context(
    request: Request,
    env: PostgressEnvironment,
) -> ServiceContext:
    writer_pool = get_async_writer_connection_pool(env)
    reader_pool = get_random_reader_connection_pool(env)
    return ServiceContext(writer_pool, reader_pool)
