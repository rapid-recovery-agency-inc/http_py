"""MySQL async connection pool management and Starlette context integration.

Provides cached async connection pools for MySQL with support for writer
and reader replicas, plus helpers for hooking into the Starlette request lifecycle.
"""

from http_py.mysql.mysql import (
    cleanup_connections_pools,
    warm_up_connections_pools,
    get_async_writer_connection_pool,
    get_async_reader_connection_pools,
    get_random_reader_connection_pool,
)
from http_py.mysql.context import (
    MysqlContext,
    MysqlContextFactory,
    MysqlContextEnhancer,
    MysqlContextProtocol,
    build_mysql_context_factory,
    MysqlContextFactoryDependency,
    build_mysql_context_dependency_factory,
)


__all__ = [
    # Pool accessors
    "cleanup_connections_pools",
    "get_async_reader_connection_pools",
    "get_async_writer_connection_pool",
    "get_random_reader_connection_pool",
    "warm_up_connections_pools",
    # Context
    "MysqlContext",
    "MysqlContextEnhancer",
    "MysqlContextFactory",
    "MysqlContextFactoryDependency",
    "MysqlContextProtocol",
    "build_mysql_context_dependency_factory",
    "build_mysql_context_factory",
]
