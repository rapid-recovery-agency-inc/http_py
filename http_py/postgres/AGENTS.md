# PostgreSQL Module

## Purpose

This module provides a minimalistic wrapper for caching PostgreSQL connection pools using psycopg3's `ConnectionPool` and `AsyncConnectionPool`. It supports writer/reader separation for applications using read replicas.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Code                         │
│                                                             │
│    pool = get_async_writer_connection_pool(env)             │
│    async with pool.connection() as conn:                    │
│        await conn.execute(...)                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Connection Pool Factory                        │
│  - get_async_writer_connection_pool(env)                    │
│  - get_sync_writer_connection_pool(env)                     │
│  - get_async_readers_connection_pools(env)                  │
│  - get_random_reader_connection_pool(env)                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌───────────────────────────────────────────────────────────────────┐
│                     Module-Level Cache                            │
│  __async_writer_cached_connection_pool: AsyncConnectionPool       │
│  __sync_writer_cached_connection_pool: ConnectionPool             │
│  __async_readers_cached_connection_pools: list[AsyncConnectionPool]│
└───────────────────────────────────────────────────────────────────┘
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
| `__init__.py` | Exports public API for connection pool management |
| `postgres.py` | Connection pool factories and lifecycle management |

## Key Functions

| Function | Description |
|----------|-------------|
| `get_async_writer_connection_pool(env)` | Get cached async pool for writes |
| `get_sync_writer_connection_pool(env)` | Get cached sync pool for writes |
| `get_async_readers_connection_pools(env)` | Get list of async pools for reads |
| `get_random_reader_connection_pool(env)` | Get random reader pool (load balancing) |
| `warm_up_connections_pools(env)` | Open and wait for all pools at startup |
| `cleanup_connections_pools()` | Close all cached pools at shutdown |

## Environment Configuration

Requires `PostgressEnvironment` protocol from `http_py.types`:

| Field | Type | Description |
|-------|------|-------------|
| `DB_USERNAME` | str | Database username |
| `DB_PASSWORD` | str | Database password |
| `DB_WRITER_HOST` | str | Primary database host |
| `DB_READER_HOSTS` | str | Comma-separated replica hosts |
| `DB_PORT` | str | Database port |
| `DB_NAME` | str | Database name |
| `DB_POOL_TIMEOUT` | int | Connection acquisition timeout (seconds) |
| `DB_MIN_POOL_SIZE` | int | Minimum connections per pool |
| `DB_MAX_POOL_SIZE` | int | Maximum connections per pool |
| `DB_POOL_MAX_IDLE_TIME_SECONDS` | int | Max idle time before connection recycling |

## Usage Example

```python
from dataclasses import dataclass
from http_py.postgres import (
    get_async_writer_connection_pool,
    get_random_reader_connection_pool,
    warm_up_connections_pools,
    cleanup_connections_pools,
)

@dataclass(frozen=True)
class AppEnv:
    DB_USERNAME: str = "postgres"
    DB_PASSWORD: str = "secret"
    DB_WRITER_HOST: str = "primary.db.local"
    DB_READER_HOSTS: str = "replica1.db.local,replica2.db.local"
    DB_PORT: str = "5432"
    DB_NAME: str = "myapp"
    DB_POOL_TIMEOUT: int = 30
    DB_MIN_POOL_SIZE: int = 2
    DB_MAX_POOL_SIZE: int = 10
    DB_POOL_MAX_IDLE_TIME_SECONDS: int = 300

env = AppEnv()

# At startup
await warm_up_connections_pools(env)

# For writes
writer_pool = get_async_writer_connection_pool(env)
async with writer_pool.connection() as conn:
    await conn.execute("INSERT INTO users (name) VALUES (%s)", ["Alice"])

# For reads (load balanced)
reader_pool = get_random_reader_connection_pool(env)
async with reader_pool.connection() as conn:
    result = await conn.execute("SELECT * FROM users")

# At shutdown
await cleanup_connections_pools()
```

## Design Principles

1. **Singleton Pools**: One pool instance per database endpoint, cached module-wide
2. **Writer/Reader Separation**: Explicit split for write-heavy vs read-heavy workloads
3. **Lazy Initialization**: Pools created on first access, not at import
4. **Explicit Warmup**: `open=False` at creation; call `warm_up_connections_pools()` at startup
5. **Random Load Balancing**: Simple random selection among reader replicas

## Known Limitations

1. **Global State**: Module-level caching makes testing harder
2. **No Connection URL Encoding**: Special characters in password may break
3. **No Health Checks**: No periodic connection validation
4. **No Retry Logic**: Connection failures not handled with backoff
5. **Single Pool Per Host**: Cannot have multiple pools with different settings

## Future Enhancements

### Planned Features

- [ ] **URL-Safe Connection Strings**: Properly encode special characters in passwords
- [ ] **Health Check Endpoint**: Periodic ping to detect stale connections
- [ ] **Connection Retry**: Exponential backoff on transient failures
- [ ] **Pool Metrics**: Expose pool stats (size, waiting, idle) for monitoring
- [ ] **Class-Based Manager**: Replace globals with `PostgresManager` class
- [ ] **Read/Write Routing**: Automatic routing based on query type
- [ ] **Connection Tagging**: Label connections for debugging
- [ ] **SSL/TLS Configuration**: Support for encrypted connections
- [ ] **Statement Timeout**: Per-connection query timeout settings

### Extension Points

1. **Custom Pool Factory**: Override pool creation for testing or custom settings
2. **Connection Hooks**: Pre/post connection callbacks for logging or metrics
3. **Load Balancer Strategy**: Pluggable selection (round-robin, least-connections)
4. **Connection Wrapper**: Add tracing, logging, or query interception

### Example: Class-Based Manager (Future)

```python
class PostgresManager:
    def __init__(self, env: PostgresEnvironment):
        self._env = env
        self._writer_pool: AsyncConnectionPool | None = None
        self._reader_pools: list[AsyncConnectionPool] = []

    async def get_writer(self) -> AsyncConnectionPool:
        if self._writer_pool is None:
            self._writer_pool = await self._create_pool(self._env.DB_WRITER_HOST)
        return self._writer_pool

    async def get_reader(self) -> AsyncConnectionPool:
        if not self._reader_pools:
            await self._init_readers()
        return random.choice(self._reader_pools)

    async def close(self) -> None:
        if self._writer_pool:
            await self._writer_pool.close()
        for pool in self._reader_pools:
            await pool.close()
```

### Migration Notes

When extending the postgres module:
1. Maintain backward compatibility with function-based API
2. Consider class-based approach for new features
3. Add URL encoding for connection strings before production use
4. Implement health checks for long-running services
5. Add metrics for pool utilization monitoring
