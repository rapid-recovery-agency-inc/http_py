"""MySQL context integration for Starlette request lifecycle."""

from __future__ import annotations

import random
from typing import Protocol
from collections.abc import Callable

import aiomysql
from starlette.requests import Request

from http_py.types import MySQLEnvironment
from http_py.mysql.mysql import (
    get_async_writer_connection_pool,
    get_async_reader_connection_pools,
)
from http_py.utils.protocols import assert_conforms_to_protocol


class MysqlContextProtocol[T](Protocol):
    writer_pool: aiomysql.Pool
    reader_pools: list[aiomysql.Pool]
    env: T
    request: Request

    @property
    def writer(self) -> aiomysql.Pool:
        """Return the writer connection pool."""
        ...

    @property
    def reader(self) -> aiomysql.Pool:
        """Return a reader connection pool (random selection for load balancing)."""
        ...


MysqlContextFactory = Callable[[Request], MysqlContextProtocol[MySQLEnvironment]]
MysqlContextEnhancer = Callable[
    [Request, MysqlContextProtocol[MySQLEnvironment]],
    MysqlContextProtocol[MySQLEnvironment],
]
MysqlContextFactoryDependency = Callable[[Request], None]


class MysqlContext[T](MysqlContextProtocol[T]):
    writer_pool: aiomysql.Pool
    reader_pools: list[aiomysql.Pool]
    env: T
    request: Request

    def __init__(
        self,
        writer_pool: aiomysql.Pool,
        reader_pools: list[aiomysql.Pool],
        env: T,
        request: Request,
    ) -> None:
        self.writer_pool = writer_pool
        self.reader_pools = reader_pools
        self.env = env
        self.request = request

    @property
    def writer(self) -> aiomysql.Pool:
        """Return the writer connection pool."""
        return self.writer_pool

    @property
    def reader(self) -> aiomysql.Pool:
        """Return a reader connection pool (random selection for load balancing)."""
        # S311: Not used for cryptography, safe to suppress
        return random.choice(self.reader_pools)  # noqa: S311


def build_mysql_context_dependency_factory(
    env: MySQLEnvironment,
    enhancers: list[MysqlContextEnhancer] | None = None,
) -> MysqlContextFactoryDependency:
    """Build a Starlette dependency that attaches a :class:`MysqlContext`
    to ``request.state.mysql_context``.

    Args:
        env: Environment conforming to :class:`~http_py.types.MySQLEnvironment`.
        enhancers: Optional callables that mutate the context after creation.

    Returns:
        A zero-return dependency callable suitable for use with ``Depends()``.
    """
    assert_conforms_to_protocol(env, MySQLEnvironment, variable_name="env")

    def dependency(request: Request) -> None:
        writer_pool = get_async_writer_connection_pool()
        reader_pools = get_async_reader_connection_pools()
        context: MysqlContext[MySQLEnvironment] = MysqlContext(
            writer_pool=writer_pool,
            reader_pools=reader_pools,
            env=env,
            request=request,
        )
        request.state.mysql_context = context
        if enhancers:
            for enhancer in enhancers:
                enhancer(request, context)

    return dependency


def build_mysql_context_factory(
    env: MySQLEnvironment,
    enhancers: list[MysqlContextEnhancer] | None = None,
) -> MysqlContextFactory:
    """Build a factory that creates and returns a :class:`MysqlContext`
    for the given request.

    Args:
        env: Environment conforming to :class:`~http_py.types.MySQLEnvironment`.
        enhancers: Optional callables that mutate the context after creation.

    Returns:
        A callable ``(request) -> MysqlContextProtocol[MySQLEnvironment]``.
    """
    assert_conforms_to_protocol(env, MySQLEnvironment, variable_name="env")

    def factory(request: Request) -> MysqlContextProtocol[MySQLEnvironment]:
        writer_pool = get_async_writer_connection_pool()
        reader_pools = get_async_reader_connection_pools()
        context: MysqlContext[MySQLEnvironment] = MysqlContext(
            writer_pool=writer_pool,
            reader_pools=reader_pools,
            env=env,
            request=request,
        )
        request.state.mysql_context = context
        if enhancers:
            for enhancer in enhancers:
                enhancer(request, context)
        return context

    return factory
