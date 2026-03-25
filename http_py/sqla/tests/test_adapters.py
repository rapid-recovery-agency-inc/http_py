import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError

from http_py.sqla.adapters import (
    SQLAlchemyCursorAdapter,
    SQLAlchemyConnectionPoolAdapter,
    create_sqlalchemy_connection_pools,
)
from http_py.database.exceptions import DatabaseTimeoutError


class _AsyncContextManagerStub:
    def __init__(self, value: object):
        self._value = value

    async def __aenter__(self) -> object:
        return self._value

    async def __aexit__(
        self,
        exc_type: object,
        exc: object,
        tb: object,
    ) -> bool:
        return False


class TestSQLAlchemyCursorAdapter(unittest.TestCase):
    def test_execute_translates_psycopg_named_parameters(self) -> None:
        async def run_test() -> None:
            connection = MagicMock()
            connection.execute = AsyncMock(return_value=MagicMock())
            cursor = SQLAlchemyCursorAdapter(connection)

            await cursor.execute(
                "SELECT * FROM rate_limit WHERE path = %(path)s",
                {"path": "/v1/test"},
            )

            statement = connection.execute.await_args.args[0]
            params = connection.execute.await_args.args[1]
            self.assertIn(":path", str(statement))
            self.assertEqual(params, {"path": "/v1/test"})

        asyncio.run(run_test())

    def test_execute_raises_backend_agnostic_timeout(self) -> None:
        async def run_test() -> None:
            connection = MagicMock()
            connection.execute = AsyncMock(
                side_effect=SQLAlchemyTimeoutError("timeout")
            )
            cursor = SQLAlchemyCursorAdapter(connection)

            with self.assertRaises(DatabaseTimeoutError):
                await cursor.execute("SELECT 1")

        asyncio.run(run_test())


class TestSQLAlchemyConnectionPoolAdapter(unittest.TestCase):
    def test_writer_pool_uses_begin(self) -> None:
        async def run_test() -> None:
            connection = MagicMock()
            engine = MagicMock()
            engine.begin.return_value = _AsyncContextManagerStub(connection)
            engine.connect.return_value = _AsyncContextManagerStub(connection)

            pool = SQLAlchemyConnectionPoolAdapter(
                engine,
                name="writer",
                transactional=True,
            )

            async with pool.connection() as adapted_connection:
                self.assertIsNotNone(adapted_connection)

            engine.begin.assert_called_once_with()
            engine.connect.assert_not_called()

        asyncio.run(run_test())

    def test_reader_pool_uses_connect(self) -> None:
        async def run_test() -> None:
            connection = MagicMock()
            engine = MagicMock()
            engine.begin.return_value = _AsyncContextManagerStub(connection)
            engine.connect.return_value = _AsyncContextManagerStub(connection)

            pool = SQLAlchemyConnectionPoolAdapter(
                engine,
                name="reader",
                transactional=False,
            )

            async with pool.connection() as adapted_connection:
                self.assertIsNotNone(adapted_connection)

            engine.connect.assert_called_once_with()
            engine.begin.assert_not_called()

        asyncio.run(run_test())

    def test_reader_pool_raises_backend_agnostic_timeout(self) -> None:
        async def run_test() -> None:
            engine = MagicMock()
            engine.connect.side_effect = SQLAlchemyTimeoutError("timeout")

            pool = SQLAlchemyConnectionPoolAdapter(
                engine,
                name="reader",
                transactional=False,
            )

            with self.assertRaises(DatabaseTimeoutError):
                async with pool.connection():
                    pass

        asyncio.run(run_test())

    def test_create_sqlalchemy_connection_pools_assigns_reader_writer_names(
        self,
    ) -> None:
        writer_engine = MagicMock()
        reader_engine_1 = MagicMock()
        reader_engine_2 = MagicMock()

        writer_pool, reader_pools = create_sqlalchemy_connection_pools(
            writer_engine=writer_engine,
            reader_engines=[reader_engine_1, reader_engine_2],
            name="client_db",
            timeout=30,
        )

        self.assertEqual(writer_pool.name, "client_db:writer")
        self.assertEqual(writer_pool.timeout, 30)
        self.assertEqual(
            [pool.name for pool in reader_pools],
            [
                "client_db:reader:0",
                "client_db:reader:1",
            ],
        )


if __name__ == "__main__":
    unittest.main()
