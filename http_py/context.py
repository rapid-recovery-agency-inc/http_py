import random
from typing import cast, Protocol
from collections.abc import Callable

from http_py.types import PostgressEnvironment
from http_py.postgres import (
    get_async_writer_connection_pool,
    get_async_readers_connection_pools,
)
from http_py.database.protocols import ConnectionPoolProtocol


class ContextProtocol(Protocol):
    writer_pool: ConnectionPoolProtocol
    reader_pools: list[ConnectionPoolProtocol]

    @property
    def writer(self) -> ConnectionPoolProtocol:
        return self.writer_pool

    @property
    def reader(self) -> ConnectionPoolProtocol:
        # S311: Not used for cryptography, safe to suppress
        return random.choice(self.reader_pools)  # noqa: S311


class ContextStateProtocol(Protocol):
    context: ContextProtocol


class RequestStateContainerProtocol(Protocol):
    state: ContextStateProtocol


ContextFactory = Callable[[object], ContextProtocol]
ContextFactoryDependency = Callable[[RequestStateContainerProtocol], None]


class Context(ContextProtocol):
    pool: ConnectionPoolProtocol
    writer_pool: ConnectionPoolProtocol
    reader_pools: list[ConnectionPoolProtocol]

    def __init__(
        self,
        writer_pool: ConnectionPoolProtocol,
        reader_pools: list[ConnectionPoolProtocol],
    ):
        self.pool = writer_pool
        self.reader_pools = reader_pools
        self.writer_pool = writer_pool


def _build_default_connection_pools(
    env: PostgressEnvironment,
) -> tuple[ConnectionPoolProtocol, list[ConnectionPoolProtocol]]:
    writer_pool = cast(ConnectionPoolProtocol, get_async_writer_connection_pool(env))
    reader_pools = [
        cast(ConnectionPoolProtocol, pool)
        for pool in get_async_readers_connection_pools(env)
    ]
    return writer_pool, reader_pools


def build_context_factory_dependency(
    env: PostgressEnvironment,
) -> ContextFactoryDependency:
    def dependency(request: RequestStateContainerProtocol) -> None:
        writer_pool, reader_pools = _build_default_connection_pools(env)
        context = Context(
            writer_pool=writer_pool,
            reader_pools=reader_pools,
        )
        request.state.context = context

    return dependency


def build_context_factory(
    env: PostgressEnvironment,
) -> ContextFactory:
    def factory(_: object) -> ContextProtocol:
        writer_pool, reader_pools = _build_default_connection_pools(env)
        # Context implements Context protocol
        return Context(
            writer_pool=writer_pool,
            reader_pools=reader_pools,
        )

    return factory
