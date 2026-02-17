# E2E Testing Module

## Purpose

This module provides end-to-end testing utilities with isolated database support. It enables tests to run against real PostgreSQL databases by creating temporary databases for each test case, ensuring complete isolation between tests.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Test Suite                               │
│                                                             │
│    class MyTests(CustomAsyncTestCase):                      │
│        env = AppEnv()                                       │
│        migrations_folder_path = "migrations/"               │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   asyncSetUp()                              │
│  1. Connect to PostgreSQL server                            │
│  2. CREATE DATABASE test_db_{pid}_{timestamp}               │
│  3. Open connection pool to new database                    │
│  4. Run all SQL migrations                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Test Execution                            │
│  - self.database_pool available for queries                 │
│  - Full database schema from migrations                     │
│  - Complete isolation from other tests                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  asyncTearDown()                            │
│  1. Close connection pool                                   │
│  2. DROP DATABASE test_db_{pid}_{timestamp}                 │
│  3. Close server connection                                 │
└─────────────────────────────────────────────────────────────┘
```

## File Structure

| File | Description |
|------|-------------|
| `__init__.py` | Exports `CustomAsyncTestCase`, `Migration`, `get_migration_files_content` |
| `services.py` | Test case base class and migration loading utilities |

## Key Components

### CustomAsyncTestCase

Base class for async tests with isolated databases. Extends `unittest.IsolatedAsyncioTestCase`.

**Class Attributes (must be set by subclass):**

| Attribute | Type | Description |
|-----------|------|-------------|
| `env` | `E2ETestEnvironment` | Environment with `TEST_DATABASE_URL` |
| `migrations_folder_path` | `str` | Path to folder containing `.sql` files |

**Instance Attributes (available in tests):**

| Attribute | Type | Description |
|-----------|------|-------------|
| `database_pool` | `AsyncConnectionPool` | Connection pool to test database |
| `db_name` | `str` | Generated database name |
| `async_connection` | `AsyncConnection` | Admin connection for DB management |

### get_migration_files_content(path) → list[Migration]

Loads and caches SQL migration files from a directory:
- Filters to `.sql` files only
- Sorts files alphabetically (use numeric prefixes: `001_init.sql`)
- Returns list of `Migration` dicts with `name` and `content`

### Migration TypedDict

```python
class Migration(TypedDict):
    name: str      # Filename (e.g., "001_init.sql")
    content: str   # SQL content
```

## Environment Configuration

Requires `E2ETestEnvironment` protocol from `http_py.types`:

| Field | Type | Description |
|-------|------|-------------|
| `TEST_DATABASE_URL` | str | PostgreSQL connection string (without database name) |

Example: `postgresql://user:pass@localhost:5432`

## Usage Example

```python
import unittest
from dataclasses import dataclass
from http_py.e2e_testing import CustomAsyncTestCase

@dataclass(frozen=True)
class TestEnv:
    TEST_DATABASE_URL: str = "postgresql://postgres:secret@localhost:5432"

class UserServiceTests(CustomAsyncTestCase):
    env = TestEnv()
    migrations_folder_path = "migrations/"

    async def test_create_user(self):
        async with self.database_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO users (name) VALUES (%s) RETURNING id",
                    ["Alice"]
                )
                result = await cur.fetchone()
                self.assertIsNotNone(result)
                self.assertEqual(result[0], 1)

    async def test_list_users(self):
        # Each test gets a fresh database
        async with self.database_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT COUNT(*) FROM users")
                result = await cur.fetchone()
                self.assertEqual(result[0], 0)  # Empty!

if __name__ == "__main__":
    unittest.main()
```

## Migration Files

Place SQL files in the migrations folder with numeric prefixes for ordering:

```
migrations/
├── 001_create_users.sql
├── 002_create_orders.sql
└── 003_add_indexes.sql
```

Each file is executed in alphabetical order during `asyncSetUp()`.

## Design Principles

1. **Complete Isolation**: Each test gets its own database, preventing test interference
2. **Real Database**: Tests run against actual PostgreSQL, not mocks
3. **Migration-Based Schema**: Same migrations as production ensure schema parity
4. **Automatic Cleanup**: Databases are dropped after each test
5. **Unique Naming**: Database names include PID and timestamp to avoid collisions
