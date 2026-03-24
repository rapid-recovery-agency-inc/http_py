import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from sqlalchemy.ext.asyncio import AsyncEngine

from http_py.sqla.context import (
    build_sqla_context_factory,
    build_sqla_context_factory_dependency,
    build_sqla_context_factory_from_engine_group,
    build_sqla_context_factory_dependency_from_engine_group,
)


class _EngineGroup:
    def __init__(
        self,
        writer: AsyncEngine,
        readers: list[AsyncEngine],
        db_name: str,
    ):
        self.writer = writer
        self._readers = readers
        self.db_name = db_name

    def readers(self) -> list[AsyncEngine]:
        return self._readers


class TestSQLAlchemyContextFactories(unittest.TestCase):
    def test_build_sqla_context_factory_returns_context(self) -> None:
        writer_engine = MagicMock()
        reader_engine = MagicMock()

        factory = build_sqla_context_factory(
            writer_engine=writer_engine,
            reader_engines=[reader_engine],
            name="example",
        )

        context = factory(MagicMock())

        self.assertEqual(context.writer_pool.name, "example:writer")
        self.assertEqual(len(context.reader_pools), 1)
        self.assertEqual(context.reader_pools[0].name, "example:reader:0")

    def test_build_sqla_context_factory_dependency_sets_request_context(self) -> None:
        writer_engine = MagicMock()
        reader_engine = MagicMock()

        dependency = build_sqla_context_factory_dependency(
            writer_engine=writer_engine,
            reader_engines=[reader_engine],
            name="example",
        )

        request = SimpleNamespace(state=SimpleNamespace())
        dependency(request)

        self.assertEqual(request.state.context.writer_pool.name, "example:writer")

    def test_engine_group_factory_uses_group_db_name_by_default(self) -> None:
        engine_group = _EngineGroup(
            writer=MagicMock(),
            readers=[MagicMock(), MagicMock()],
            db_name="foundd_client",
        )

        factory = build_sqla_context_factory_from_engine_group(engine_group)
        context = factory(MagicMock())

        self.assertEqual(context.writer_pool.name, "foundd_client:writer")
        self.assertEqual(
            [pool.name for pool in context.reader_pools],
            ["foundd_client:reader:0", "foundd_client:reader:1"],
        )

    def test_engine_group_factory_allows_name_override(self) -> None:
        engine_group = _EngineGroup(
            writer=MagicMock(),
            readers=[MagicMock()],
            db_name="foundd_client",
        )

        factory = build_sqla_context_factory_from_engine_group(
            engine_group,
            name="override",
        )
        context = factory(MagicMock())

        self.assertEqual(context.writer_pool.name, "override:writer")

    def test_engine_group_dependency_sets_request_context(self) -> None:
        engine_group = _EngineGroup(
            writer=MagicMock(),
            readers=[MagicMock()],
            db_name="foundd_client",
        )

        dependency = build_sqla_context_factory_dependency_from_engine_group(
            engine_group,
        )

        request = SimpleNamespace(state=SimpleNamespace())
        dependency(request)

        self.assertEqual(
            request.state.context.writer_pool.name,
            "foundd_client:writer",
        )


if __name__ == "__main__":
    unittest.main()
