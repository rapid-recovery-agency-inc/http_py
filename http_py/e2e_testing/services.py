import os
import time
import unittest
from typing import TypedDict

import psycopg
from psycopg import sql
from psycopg_pool import AsyncConnectionPool

from http_py.types import E2ETestEnvironment
from http_py.logging.services import create_logger


logger = create_logger(__name__)


class Migration(TypedDict):
    name: str
    content: str


__migrations_content: list[Migration] = []


def get_migration_files_content(migration_folder_path: str) -> list[Migration]:
    global __migrations_content  # noqa: PLW0602
    if len(__migrations_content) > 0:
        return __migrations_content
    migration_files = []
    for file in os.listdir(migration_folder_path):
        if file.endswith(".sql"):
            migration_files.append(file)
        else:
            logger.warning(
                f"get_migration_files_content: Skipping non-SQL file "
                f"'{file}' in '{migration_folder_path}'"
            )
    migration_files.sort()
    for file in migration_files:
        with open(os.path.join(migration_folder_path, file)) as f:
            __migrations_content.append(Migration(name=file, content=f.read()))
    return __migrations_content


class CustomAsyncTestCase(unittest.IsolatedAsyncioTestCase):
    """Async test case with isolated database per test.

    Subclasses must set `env` and `migrations_folder_path` class attributes.
    """

    env: E2ETestEnvironment | None = None
    migrations_folder_path: str | None = None

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        if self.env is None:
            raise ValueError("CustomAsyncTestCase: 'env' must be set before asyncSetUp")
        if self.migrations_folder_path is None:
            raise ValueError(
                "CustomAsyncTestCase: 'migrations_folder_path' must be set "
                "before asyncSetUp"
            )
        connection_string = self.env.TEST_DATABASE_URL
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
        migrations = get_migration_files_content(self.migrations_folder_path)
        async with self.database_pool.connection() as conn:
            async with conn.cursor() as cur:
                for migration in migrations:
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
