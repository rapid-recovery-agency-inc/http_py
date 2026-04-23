import random
from typing import Protocol
from collections.abc import Callable

from psycopg_pool import AsyncConnectionPool
from starlette.requests import Request

from http_py.types import PostgressEnvironment
from http_py.postgres import (
    get_async_writer_connection_pool,
    get_async_readers_connection_pools,
)
from http_py.utils.protocols import assert_conforms_to_protocol


class ContextProtocol[T](Protocol):
    writer_pool: AsyncConnectionPool
    reader_pools: list[AsyncConnectionPool]
    env: T
    request: Request

    @property
    def writer(self) -> AsyncConnectionPool:
        """Return the writer connection pool."""
        ...

    @property
    def reader(self) -> AsyncConnectionPool:
        """Return a reader connection pool (random selection for load balancing)."""
        ...


ContextFactory = Callable[[Request], ContextProtocol[PostgressEnvironment]]
ContextEnhancer = Callable[
    [Request, ContextProtocol[PostgressEnvironment]],
    ContextProtocol[PostgressEnvironment],
]
ContextFactoryDependency = Callable[[Request], None]


class Context[T](ContextProtocol[T]):
    pool: AsyncConnectionPool
    writer_pool: AsyncConnectionPool
    reader_pools: list[AsyncConnectionPool]
    env: T
    request: Request

    def __init__(
        self,
        writer_pool: AsyncConnectionPool,
        reader_pools: list[AsyncConnectionPool],
        env: T,
        request: Request,
    ):
        self.reader_pools = reader_pools
        self.writer_pool = writer_pool
        self.env = env
        self.request = request

    @property
    def writer(self) -> AsyncConnectionPool:
        """Return the writer connection pool."""
        return self.writer_pool

    @property
    def reader(self) -> AsyncConnectionPool:
        """Return a reader connection pool (random selection for load balancing)."""
        # S311: Not used for cryptography, safe to suppress
        return random.choice(self.reader_pools)  # noqa: S311


def build_context_dependency_factory(
    env: PostgressEnvironment, enhancers: list[ContextEnhancer] | None = None
) -> ContextFactoryDependency:
    assert_conforms_to_protocol(
        env,
        PostgressEnvironment,
        variable_name="env",
    )

    def dependency(request: Request) -> None:
        writer_pool = get_async_writer_connection_pool(env)
        reader_pools = get_async_readers_connection_pools(env)
        context = Context(
            writer_pool=writer_pool,
            reader_pools=reader_pools,
            env=env,
            request=request,
        )
        request.state.context = context
        if enhancers:
            for enhancer in enhancers:
                enhancer(request, context)

    return dependency


def build_context_factory(
    env: PostgressEnvironment, enhancers: list[ContextEnhancer] | None = None
) -> ContextFactory:
    assert_conforms_to_protocol(
        env,
        PostgressEnvironment,
        variable_name="env",
    )

    def factory(request: Request) -> ContextProtocol[PostgressEnvironment]:
        writer_pool = get_async_writer_connection_pool(env)
        reader_pools = get_async_readers_connection_pools(env)
        # Context implements Context protocol
        context = Context(
            writer_pool=writer_pool,
            reader_pools=reader_pools,
            env=env,
            request=request,
        )
        request.state.context = context
        if enhancers:
            for enhancer in enhancers:
                enhancer(request, context)
        return context

    return factory
