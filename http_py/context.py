import random
from typing import Protocol
from collections.abc import Callable, Awaitable

from psycopg_pool import AsyncConnectionPool
from starlette.requests import Request

from http_py.types import PostgressEnvironment
from http_py.postgres import (
    get_async_writer_connection_pool,
    get_async_readers_connection_pools,
)


class ContextProtocol(Protocol):
    writer_pool: AsyncConnectionPool
    reader_pools: list[AsyncConnectionPool]

    @property
    def writer(self) -> AsyncConnectionPool:
        return self.writer_pool

    @property
    def reader(self) -> AsyncConnectionPool:
        # S311: Not used for cryptography, safe to suppress
        return random.choice(self.reader_pools)  # noqa: S311


ContextFactory = Callable[[Request], Awaitable[ContextProtocol]]
ContextFactoryDependency = Callable[[Request], None]


class Context(ContextProtocol):
    pool: AsyncConnectionPool
    writer_pool: AsyncConnectionPool
    reader_pools: list[AsyncConnectionPool]

    def __init__(
        self,
        writer_pool: AsyncConnectionPool,
        reader_pools: list[AsyncConnectionPool],
    ):
        self.reader_pools = reader_pools
        self.writer_pool = writer_pool


def build_context_factory_dependency(
    env: PostgressEnvironment,
) -> ContextFactoryDependency:
    def dependency(request: Request) -> None:
        writer_pool = get_async_writer_connection_pool(env)
        reader_pools = get_async_readers_connection_pools(env)
        context = Context(
            writer_pool=writer_pool,
            reader_pools=reader_pools,
        )
        request.state.context = context

    return dependency


async def build_context_factory(
    env: PostgressEnvironment,
) -> ContextFactory:
    writer_pool = get_async_writer_connection_pool(env)
    reader_pools = get_async_readers_connection_pools(env)

    async def factory(_: Request) -> ContextProtocol:
        # Context implements Context protocol
        return Context(
            writer_pool=writer_pool,
            reader_pools=reader_pools,
        )

    return factory
