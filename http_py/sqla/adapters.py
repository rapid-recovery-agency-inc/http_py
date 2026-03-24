import re
from typing import Any, cast
from contextlib import asynccontextmanager
from collections.abc import Sequence, AsyncIterator

from sqlalchemy import text
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection

from http_py.database.protocols import (
    ConnectionPoolProtocol,
    DatabaseCursorProtocol,
    DatabaseConnectionProtocol,
)
from http_py.database.exceptions import DatabaseTimeoutError


_SQL_PARAM_PATTERN = re.compile(r"%\((?P<name>[A-Za-z_][A-Za-z0-9_]*)\)s")


def _translate_query(query: str) -> str:
    return _SQL_PARAM_PATTERN.sub(r":\g<name>", query)


class SQLAlchemyCursorAdapter(DatabaseCursorProtocol):
    def __init__(self, connection: AsyncConnection):
        self._connection = connection
        self._result: Any | None = None

    async def execute(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        statement = text(_translate_query(query))
        try:
            self._result = await self._connection.execute(statement, params or {})
        except SQLAlchemyTimeoutError as err:
            raise DatabaseTimeoutError(str(err)) from err
        return self._result

    async def fetchone(self) -> tuple[Any, ...] | None:
        if self._result is None:
            return None
        row = self._result.fetchone()
        if row is None:
            return None
        return tuple(row)

    @property
    def rowcount(self) -> int | None:
        if self._result is None:
            return None
        return cast(int, self._result.rowcount)


class SQLAlchemyConnectionAdapter(DatabaseConnectionProtocol):
    def __init__(self, connection: AsyncConnection):
        self._connection = connection

    @asynccontextmanager
    async def cursor(self) -> AsyncIterator[SQLAlchemyCursorAdapter]:
        yield SQLAlchemyCursorAdapter(self._connection)


class SQLAlchemyConnectionPoolAdapter(ConnectionPoolProtocol):
    def __init__(
        self,
        engine: AsyncEngine,
        name: str,
        *,
        transactional: bool,
        timeout: int | float | None = None,
    ):
        self._engine = engine
        self._transactional = transactional
        self.name = name
        self.timeout = timeout

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[SQLAlchemyConnectionAdapter]:
        try:
            if self._transactional:
                async with self._engine.begin() as connection:
                    yield SQLAlchemyConnectionAdapter(connection)
            else:
                async with self._engine.connect() as connection:
                    yield SQLAlchemyConnectionAdapter(connection)
        except SQLAlchemyTimeoutError as err:
            raise DatabaseTimeoutError(str(err)) from err

    def get_stats(self) -> dict[str, Any]:
        return {
            "backend": "sqlalchemy",
            "name": self.name,
            "timeout": self.timeout,
            "url": str(self._engine.url),
        }


def create_sqlalchemy_connection_pools(
    writer_engine: AsyncEngine,
    reader_engines: Sequence[AsyncEngine],
    *,
    name: str = "sqlalchemy",
    timeout: int | float | None = None,
) -> tuple[ConnectionPoolProtocol, list[ConnectionPoolProtocol]]:
    writer_pool: ConnectionPoolProtocol = SQLAlchemyConnectionPoolAdapter(
        writer_engine,
        name=f"{name}:writer",
        transactional=True,
        timeout=timeout,
    )
    reader_pools: list[ConnectionPoolProtocol] = [
        SQLAlchemyConnectionPoolAdapter(
            reader_engine,
            name=f"{name}:reader:{index}",
            transactional=False,
            timeout=timeout,
        )
        for index, reader_engine in enumerate(reader_engines)
    ]
    return writer_pool, reader_pools
