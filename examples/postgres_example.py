"""Examples: http_py.postgres module usage.

This example demonstrates PostgreSQL connection pool management
with writer/reader separation for high-availability setups.
"""

from typing import Protocol
from dataclasses import dataclass

from psycopg_pool import AsyncConnectionPool

from http_py.postgres import (
    cleanup_connections_pools,
    warm_up_connections_pools,
    get_sync_writer_connection_pool,
    get_async_writer_connection_pool,
    get_random_reader_connection_pool,
    get_async_readers_connection_pools,
)


# ──────────────────────────────────────────────────────────────────────
# 1. Environment Configuration (must implement PostgressEnvironment)
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class DatabaseEnv:
    """Database configuration implementing PostgressEnvironment protocol."""

    DB_USERNAME: str
    DB_PASSWORD: str
    DB_WRITER_HOST: str
    DB_READER_HOSTS: str  # Comma-separated: "reader1.example.com,reader2.example.com"
    DB_PORT: str = "5432"
    DB_NAME: str = "mydb"
    DB_POOL_TIMEOUT: int = 30
    DB_MIN_POOL_SIZE: int = 1
    DB_MAX_POOL_SIZE: int = 10
    DB_POOL_MAX_IDLE_TIME_SECONDS: int = 300


# ──────────────────────────────────────────────────────────────────────
# 2. Connection Pool Lifecycle
# ──────────────────────────────────────────────────────────────────────


async def pool_lifecycle_example(env: DatabaseEnv) -> None:
    """Initialize and close connection pools."""
    # Get pools (lazy-created on first access)
    writer_pool = get_async_writer_connection_pool(env)  # For INSERT/UPDATE/DELETE
    reader_pool = get_random_reader_connection_pool(env)  # Random read replica

    # Warm up pools on application startup
    await warm_up_connections_pools(env)

    # ... use pools for database operations ...

    # Close on application shutdown
    await cleanup_connections_pools()


# ──────────────────────────────────────────────────────────────────────
# 3. Basic Database Operations
# ──────────────────────────────────────────────────────────────────────


async def create_user(pool: AsyncConnectionPool, name: str, email: str) -> int:
    """Insert a new user and return the ID."""
    async with pool.connection() as conn:
        result = await conn.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id",
            (name, email),
        )
        row = await result.fetchone()
        return row[0]  # -> user_id


async def get_user(pool: AsyncConnectionPool, user_id: int) -> dict | None:
    """Fetch a user by ID."""
    async with pool.connection() as conn:
        result = await conn.execute(
            "SELECT id, name, email FROM users WHERE id = %s",
            (user_id,),
        )
        row = await result.fetchone()
        if row:
            return {"id": row[0], "name": row[1], "email": row[2]}
        return None


async def list_users(pool: AsyncConnectionPool, limit: int = 100) -> list[dict]:
    """List all users."""
    async with pool.connection() as conn:
        result = await conn.execute(
            "SELECT id, name, email FROM users ORDER BY id LIMIT %s",
            (limit,),
        )
        rows = await result.fetchall()
        return [{"id": r[0], "name": r[1], "email": r[2]} for r in rows]


# ──────────────────────────────────────────────────────────────────────
# 4. Transaction Management
# ──────────────────────────────────────────────────────────────────────


async def transfer_funds(
    pool: AsyncConnectionPool,
    from_account: int,
    to_account: int,
    amount: float,
) -> bool:
    """Transfer funds between accounts atomically."""
    async with pool.connection() as conn:
        async with conn.transaction():
            # Debit source account
            await conn.execute(
                "UPDATE accounts SET balance = balance - %s WHERE id = %s",
                (amount, from_account),
            )

            # Credit destination account
            await conn.execute(
                "UPDATE accounts SET balance = balance + %s WHERE id = %s",
                (amount, to_account),
            )

            # If any operation fails, entire transaction rolls back
            return True


# ──────────────────────────────────────────────────────────────────────
# 5. FastAPI Integration
# ──────────────────────────────────────────────────────────────────────


# from fastapi import FastAPI
# from contextlib import asynccontextmanager
# from http_py.postgres import (
#     get_async_writer_connection_pool,
#     get_random_reader_connection_pool,
#     warm_up_connections_pools,
#     cleanup_connections_pools,
# )
#
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup - warm up connection pools
#     await warm_up_connections_pools(env)
#     yield
#     # Shutdown - close all pools
#     await cleanup_connections_pools()
#
# app = FastAPI(lifespan=lifespan)
#
# @app.get("/users/{user_id}")
# async def get_user_endpoint(user_id: int):
#     pool = get_random_reader_connection_pool(env)  # Uses read replica
#     user = await get_user(pool, user_id)
#     if user:
#         return user
#     return {"error": "User not found"}
#
# @app.post("/users")
# async def create_user_endpoint(name: str, email: str):
#     pool = get_async_writer_connection_pool(env)  # Uses primary
#     user_id = await create_user(pool, name, email)
#     return {"id": user_id}


# ──────────────────────────────────────────────────────────────────────
# 6. Writer/Reader Separation Pattern
# ──────────────────────────────────────────────────────────────────────

# Configure DB_READER_HOSTS with multiple replicas:
#
# @dataclass(frozen=True)
# class ProdEnv:
#     DB_WRITER_HOST: str = "db-primary.example.com"
#     DB_READER_HOSTS: str = "db-replica-1.example.com,db-replica-2.example.com"
#     ...
#
# Usage pattern:
# - get_async_writer_connection_pool(env) -> routes to primary
# - get_random_reader_connection_pool(env) -> routes to random replica
# - get_async_readers_connection_pools(env) -> get all reader pools
#
# Benefits:
# - Distributes read load across replicas
# - Primary handles only writes
# - Improved query performance and scalability
