# MySQL Module

## Purpose

This module provides a minimalistic wrapper for caching async MySQL connection pools using `aiomysql`. It supports writer/reader separation for applications using read replicas and integrates with the Starlette request lifecycle via `MysqlContext`.

> **Key difference from the PostgreSQL module:** `aiomysql.create_pool()` is a coroutine, so pool *creation* must happen inside `warm_up_connections_pools(env)` at application startup. The pool accessor functions (`get_async_writer_connection_pool`, etc.) return the already-created cached pools and raise `RuntimeError` if warm-up has not been called.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Code                         │
│                                                             │
│    pool = get_async_writer_connection_pool()                │
│    async with pool.acquire() as conn:                       │
│        await conn.execute(...)                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Connection Pool Accessors                      │
│  - get_async_writer_connection_pool()                       │
│  - get_async_reader_connection_pools()                      │
│  - get_random_reader_connection_pool()                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Module-Level Cache                           │
│  __async_writer_cached_pool: aiomysql.Pool | None               │
│  __async_reader_cached_pools: list[aiomysql.Pool] | None        │
└──────────────────────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌───────────────┬───────────────┬───────────────┐
│  Writer Pool  │  Reader Pool  │  Reader Pool  │
│   (Primary)   │  (Replica 1)  │  (Replica N)  │
└───────────────┴───────────────┴───────────────┘
```

## File Structure

| File | Description |
|------|-------------|
| `__init__.py` | Exports all public symbols from `mysql.py` and `context.py` |
| `mysql.py` | Pool creation, lifecycle (`warm_up` / `cleanup`), and cached accessors |
| `context.py` | `MysqlContext` class and Starlette dependency/factory builders |
| `AGENTS.md` | This file |

## Key Functions

### Pool lifecycle

| Function | Description |
|----------|-------------|
| `warm_up_connections_pools(env)` | **Must be called at startup.** Creates writer + all reader pools |
| `cleanup_connections_pools()` | Closes all cached pools at shutdown |

### Pool accessors

| Function | Description |
|----------|-------------|
| `get_async_writer_connection_pool()` | Returns cached writer pool (raises `RuntimeError` if not warmed up) |
| `get_async_reader_connection_pools()` | Returns list of cached reader pools |
| `get_random_reader_connection_pool()` | Returns a random reader pool for load balancing |

### Context integration

| Function / Class | Description |
|-----------------|-------------|
| `MysqlContext[T]` | Concrete context object carrying `writer_pool`, `reader_pools`, `env`, `request` |
| `MysqlContextProtocol[T]` | Structural protocol for type-checking context objects |
| `build_mysql_context_dependency_factory(env, enhancers)` | Returns a Starlette `Depends`-compatible callable; sets `request.state.mysql_context` |
| `build_mysql_context_factory(env, enhancers)` | Returns a factory `(request) -> MysqlContextProtocol` |

## Environment Configuration

Requires `MySQLEnvironment` protocol from `http_py.types`:

| Field | Type | Description |
|-------|------|-------------|
| `MYSQL_USERNAME` | str | Database username |
| `MYSQL_PASSWORD` | str | Database password |
| `MYSQL_WRITER_HOST` | str | Primary database host |
| `MYSQL_READER_HOSTS` | str | Comma-separated replica hosts |
| `MYSQL_PORT` | int | Database port (typically `3306`) |
| `MYSQL_DB_NAME` | str | Database name |
| `MYSQL_POOL_MIN_SIZE` | int | Minimum connections per pool |
| `MYSQL_POOL_MAX_SIZE` | int | Maximum connections per pool |
| `MYSQL_CONNECT_TIMEOUT` | int | Connection acquisition timeout (seconds) |
| `MYSQL_POOL_RECYCLE` | int | Seconds before a connection is recycled (-1 to disable) |

## Usage Example

```python
from dataclasses import dataclass
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request

from http_py.mysql import (
    warm_up_connections_pools,
    cleanup_connections_pools,
    build_mysql_context_dependency_factory,
)
from http_py.types import MySQLEnvironment


@dataclass(frozen=True)
class AppEnv:
    MYSQL_USERNAME: str = "app"
    MYSQL_PASSWORD: str = "secret"
    MYSQL_WRITER_HOST: str = "primary.db.local"
    MYSQL_READER_HOSTS: str = "replica1.db.local,replica2.db.local"
    MYSQL_PORT: int = 3306
    MYSQL_DB_NAME: str = "myapp"
    MYSQL_POOL_MIN_SIZE: int = 2
    MYSQL_POOL_MAX_SIZE: int = 10
    MYSQL_CONNECT_TIMEOUT: int = 10
    MYSQL_POOL_RECYCLE: int = 3600


env = AppEnv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await warm_up_connections_pools(env)
    yield
    await cleanup_connections_pools()


app = FastAPI(lifespan=lifespan)

mysql_context_dep = build_mysql_context_dependency_factory(env)


@app.get("/users")
async def list_users(request: Request, _=Depends(mysql_context_dep)):
    ctx = request.state.mysql_context
    async with ctx.reader.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id, name FROM users")
            rows = await cur.fetchall()
    return {"users": rows}
```
