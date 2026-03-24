from typing import Any, Protocol, runtime_checkable
from contextlib import AbstractAsyncContextManager


@runtime_checkable
class DatabaseCursorProtocol(Protocol):
    async def execute(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> Any: ...

    async def fetchone(self) -> tuple[Any, ...] | None: ...

    @property
    def rowcount(self) -> int | None: ...


@runtime_checkable
class DatabaseConnectionProtocol(Protocol):
    def cursor(self) -> AbstractAsyncContextManager[DatabaseCursorProtocol]: ...


@runtime_checkable
class ConnectionPoolProtocol(Protocol):
    name: str
    timeout: int | float | None

    def connection(self) -> AbstractAsyncContextManager[DatabaseConnectionProtocol]: ...

    def get_stats(self) -> dict[str, Any]: ...
