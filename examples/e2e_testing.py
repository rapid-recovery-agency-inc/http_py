"""Examples: http_py.e2e_testing module usage.

This example demonstrates end-to-end testing utilities
with isolated database support for each test.
"""

from typing import Any
from dataclasses import dataclass

from http_py.e2e_testing import CustomAsyncTestCase, get_migration_files_content


# ──────────────────────────────────────────────────────────────────────
# 1. Environment Configuration (implements E2ETestEnvironment)
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class TestEnv:
    """Test environment implementing E2ETestEnvironment protocol."""

    TEST_DATABASE_URL: str = "postgresql://postgres:password@localhost:5432"


# ──────────────────────────────────────────────────────────────────────
# 2. Basic Test Case
# ──────────────────────────────────────────────────────────────────────


class TestUserService(CustomAsyncTestCase):
    """Tests with isolated database per test method."""

    env = TestEnv()  # Required: implements E2ETestEnvironment
    migrations_folder_path = "migrations"  # Required: path to SQL migrations

    async def test_create_user(self) -> None:
        """Each test gets a fresh, isolated database."""
        async with self.database_pool.connection() as conn:
            # Insert
            await conn.execute(
                "INSERT INTO users (name, email) VALUES (%s, %s)",
                ("Alice", "alice@example.com"),
            )

            # Verify
            result = await conn.execute(
                "SELECT name, email FROM users WHERE email = %s",
                ("alice@example.com",),
            )
            row = await result.fetchone()

            self.assertEqual(row[0], "Alice")
            self.assertEqual(row[1], "alice@example.com")

    async def test_user_not_found(self) -> None:
        """This test has its own isolated database - empty tables."""
        async with self.database_pool.connection() as conn:
            result = await conn.execute(
                "SELECT COUNT(*) FROM users",
            )
            row = await result.fetchone()
            self.assertEqual(row[0], 0)  # Empty - isolated from other tests


# ──────────────────────────────────────────────────────────────────────
# 3. Test with Setup
# ──────────────────────────────────────────────────────────────────────


class TestWithSetup(CustomAsyncTestCase):
    """Test case with setup method for test data."""

    env = TestEnv()
    migrations_folder_path = "migrations"

    async def asyncSetUp(self) -> None:
        """Create test fixtures before each test."""
        await super().asyncSetUp()

        # Insert test data
        async with self.database_pool.connection() as conn:
            await conn.execute(
                "INSERT INTO users (id, name, email) VALUES (%s, %s, %s)",
                (1, "Test User", "test@example.com"),
            )

    async def test_find_user(self) -> None:
        """Test uses data from asyncSetUp."""
        async with self.database_pool.connection() as conn:
            result = await conn.execute(
                "SELECT name FROM users WHERE id = %s",
                (1,),
            )
            row = await result.fetchone()
            self.assertEqual(row[0], "Test User")


# ──────────────────────────────────────────────────────────────────────
# 4. Testing API Endpoints
# ──────────────────────────────────────────────────────────────────────


# from fastapi import FastAPI
# from fastapi.testclient import TestClient
#
# class TestAPIEndpoints(CustomAsyncTestCase):
#     '''Test FastAPI endpoints with isolated database.'''
#
#     env = TestEnv()
#     migrations_folder_path = "migrations"
#
#     async def asyncSetUp(self):
#         await super().asyncSetUp()
#
#         # Override dependency to use test database pool
#         from myapp.main import app, get_db_pool
#         app.dependency_overrides[get_db_pool] = lambda: self.database_pool
#
#         # Create test data
#         async with self.database_pool.connection() as conn:
#             await conn.execute(
#                 "INSERT INTO users (id, name) VALUES (1, 'Alice')"
#             )
#
#     async def test_get_user_endpoint(self):
#         from myapp.main import app
#
#         with TestClient(app) as client:
#             response = client.get("/users/1")
#             self.assertEqual(response.status_code, 200)
#             self.assertEqual(response.json()["name"], "Alice")


# ──────────────────────────────────────────────────────────────────────
# 5. Loading Fixture Data
# ──────────────────────────────────────────────────────────────────────


class TestWithFixtures(CustomAsyncTestCase):
    """Load test data from JSON fixture files."""

    env = TestEnv()
    migrations_folder_path = "migrations"

    @staticmethod
    def load_fixture(path: str) -> list[dict]:
        """Load fixture data from JSON file."""
        import json

        with open(path) as f:
            return json.load(f)

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()

        # Load and insert fixture data
        users = self.load_fixture("tests/fixtures/users.json")

        async with self.database_pool.connection() as conn:
            for user in users:
                await conn.execute(
                    "INSERT INTO users (name, email) VALUES (%s, %s)",
                    (user["name"], user["email"]),
                )

    async def test_fixture_data_loaded(self) -> None:
        async with self.database_pool.connection() as conn:
            result = await conn.execute("SELECT COUNT(*) FROM users")
            row = await result.fetchone()
            self.assertGreater(row[0], 0)


# ──────────────────────────────────────────────────────────────────────
# 6. Migration Files Structure
# ──────────────────────────────────────────────────────────────────────

# migrations/
# ├── 001_create_users.sql
# ├── 002_create_posts.sql
# └── 003_add_indexes.sql
#
# Example: 001_create_users.sql
# ```sql
# CREATE TABLE IF NOT EXISTS users (
#     id SERIAL PRIMARY KEY,
#     name VARCHAR(255) NOT NULL,
#     email VARCHAR(255) UNIQUE NOT NULL,
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# );
# ```


# ──────────────────────────────────────────────────────────────────────
# 7. Running Tests
# ──────────────────────────────────────────────────────────────────────

# poetry run pytest tests/                                    # All tests
# poetry run pytest tests/test_users.py                       # Single file
# poetry run pytest tests/test_users.py::TestUserService      # Single class
# poetry run pytest tests/ -v                                 # Verbose
# poetry run pytest tests/ --cov=myapp --cov-report=html      # Coverage


# ──────────────────────────────────────────────────────────────────────
# 8. Best Practices
# ──────────────────────────────────────────────────────────────────────

# 1. Each test gets isolated database - prevents test pollution
#
# 2. Follow AAA pattern:
#    - Arrange: Set up test data
#    - Act: Perform the action
#    - Assert: Verify the result
#
# 3. Test both success and failure cases
#
# 4. Use descriptive test names:
#    - Good: test_user_creation_with_valid_email_succeeds
#    - Bad: test_1, test_user
#
# 5. Keep tests focused - one assertion per test when possible
