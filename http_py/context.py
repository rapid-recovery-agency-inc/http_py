import random
from typing import Protocol
from collections.abc import Callable, Awaitable

from psycopg_pool import AsyncConnectionPool

from http_py.types import PostgressEnvironment
from http_py.request import Request
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
ContextFactoryDependency = Callable[[Request], Awaitable[None]]


class ServiceContext(ContextProtocol):
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


async def build_context_factory_dependency(
    env: PostgressEnvironment,
) -> ContextFactoryDependency:
    writer_pool = get_async_writer_connection_pool(env)
    reader_pools = get_async_readers_connection_pools(env)

    async def factory(request: Request) -> None:
        service_context = ServiceContext(
            writer_pool=writer_pool,
            reader_pools=reader_pools,
        )
        # Defensive: ensure state exists
        if not hasattr(request, "state"):
            request.state = type("state", (), {})()
        request.state.service_context = service_context  # type: ignore[attr-defined]

    return factory


async def build_context_factory(
    env: PostgressEnvironment,
) -> ContextFactory:
    writer_pool = get_async_writer_connection_pool(env)
    reader_pools = get_async_readers_connection_pools(env)

    async def factory(_: Request) -> ContextProtocol:
        # ServiceContext implements Context protocol
        return ServiceContext(
            writer_pool=writer_pool,
            reader_pools=reader_pools,
        )

    return factory
