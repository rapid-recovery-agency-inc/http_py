from typing import Protocol
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncEngine

from http_py.context import (
    Context,
    ContextFactory,
    ContextFactoryDependency,
    RequestStateContainerProtocol,
)
from http_py.sqla.adapters import create_sqlalchemy_connection_pools


class SupportsWriterAndReaders(Protocol):
    @property
    def writer(self) -> AsyncEngine: ...

    def readers(self) -> Sequence[AsyncEngine]: ...


def _build_context_from_engines(
    writer_engine: AsyncEngine,
    reader_engines: Sequence[AsyncEngine],
    *,
    name: str,
    timeout: int | float | None,
) -> tuple[ContextFactory, ContextFactoryDependency]:
    writer_pool, reader_pools = create_sqlalchemy_connection_pools(
        writer_engine,
        reader_engines,
        name=name,
        timeout=timeout,
    )

    def factory(_: object) -> Context:
        return Context(
            writer_pool=writer_pool,
            reader_pools=list(reader_pools),
        )

    def dependency(request: RequestStateContainerProtocol) -> None:
        request.state.context = Context(
            writer_pool=writer_pool,
            reader_pools=list(reader_pools),
        )

    return factory, dependency


def _resolve_engine_group_name(
    engine_group: SupportsWriterAndReaders,
    name: str | None,
) -> str:
    if name is not None:
        return name

    group_name = getattr(engine_group, "db_name", None)
    if isinstance(group_name, str) and group_name:
        return group_name

    return "sqlalchemy"


def build_sqla_context_factory(
    writer_engine: AsyncEngine,
    reader_engines: Sequence[AsyncEngine],
    *,
    name: str = "sqlalchemy",
    timeout: int | float | None = None,
) -> ContextFactory:
    factory, _ = _build_context_from_engines(
        writer_engine,
        reader_engines,
        name=name,
        timeout=timeout,
    )

    return factory


def build_sqla_context_factory_dependency(
    writer_engine: AsyncEngine,
    reader_engines: Sequence[AsyncEngine],
    *,
    name: str = "sqlalchemy",
    timeout: int | float | None = None,
) -> ContextFactoryDependency:
    _, dependency = _build_context_from_engines(
        writer_engine,
        reader_engines,
        name=name,
        timeout=timeout,
    )

    return dependency


def build_sqla_context_factory_from_engine_group(
    engine_group: SupportsWriterAndReaders,
    *,
    name: str | None = None,
    timeout: int | float | None = None,
) -> ContextFactory:
    resolved_name = _resolve_engine_group_name(engine_group, name)
    factory, _ = _build_context_from_engines(
        writer_engine=engine_group.writer,
        reader_engines=engine_group.readers(),
        name=resolved_name,
        timeout=timeout,
    )

    return factory


def build_sqla_context_factory_dependency_from_engine_group(
    engine_group: SupportsWriterAndReaders,
    *,
    name: str | None = None,
    timeout: int | float | None = None,
) -> ContextFactoryDependency:
    resolved_name = _resolve_engine_group_name(engine_group, name)
    _, dependency = _build_context_from_engines(
        writer_engine=engine_group.writer,
        reader_engines=engine_group.readers(),
        name=resolved_name,
        timeout=timeout,
    )

    return dependency
