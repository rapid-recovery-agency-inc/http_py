import os
import time
import unittest
from typing import cast, TypedDict
from unittest.mock import Mock, patch

import psycopg
from psycopg import sql
from psycopg_pool import AsyncConnectionPool

from shared.context import ServiceContext
from modules.logging.logging import create_logger
from shared.environment import env


logger = create_logger(__name__)


class Migration(TypedDict):
    name: str
    content: str


__migrations_content: list[Migration] = []


def get_migration_files_content() -> list[Migration]:
    global __migrations_content  # noqa: PLW0602
    if len(__migrations_content) > 0:
        return __migrations_content
    migrations_dir = os.path.join("etc", "migrations")
    migration_files = []
    for file in os.listdir(migrations_dir):
        if file.endswith(".sql"):
            migration_files.append(file)
    migration_files.sort()
    for file in migration_files:
        with open(os.path.join(migrations_dir, file)) as f:
            __migrations_content.append(Migration(name=file, content=f.read()))
    return __migrations_content


class CustomAsyncTestCase(unittest.IsolatedAsyncioTestCase):
    service_context: ServiceContext | None = None

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        connection_string = env().TEST_DATABASE_URL
        self.db_name = f"test_db_{os.getpid()}_{int(time.time())}"
        self.async_connection = await psycopg.AsyncConnection.connect(
            connection_string,
            autocommit=True,
        )
        async with self.async_connection.cursor() as cur:
            query = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.db_name))
            await cur.execute(query)

        self.database_pool = AsyncConnectionPool(
            conninfo=f"{connection_string}/{self.db_name}",
            open=False,
        )
        await self.database_pool.open()
        async with self.database_pool.connection() as conn:
            async with conn.cursor() as cur:
                for migration in get_migration_files_content():
                    await cur.execute(migration["content"])

    async def asyncTearDown(self) -> None:
        await super().asyncTearDown()
        await self.database_pool.close()
        async with self.async_connection.cursor() as cur:
            query = sql.SQL("DROP DATABASE {}").format(sql.Identifier(self.db_name))
            await cur.execute(query)
        await self.async_connection.close()
        self.database_pool = None
        self.async_connection = None

    def get_service_context(self) -> ServiceContext:
        if self.service_context is not None:
            return self.service_context

        self.service_context = ServiceContext(
            writer_pool=self.database_pool,
            reader_pool=self.database_pool,
        )
        return self.service_context

    def setUp(self) -> None:
        super().setUp()
        patched_load_env: Mock = cast(Mock, patch("shared.environment.load_env"))
        patched_load_env.return_value = None


class CustomTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        patched_load_env: Mock = cast(Mock, patch("shared.environment.load_env"))
        patched_load_env.return_value = None
