# Logging Module

## Purpose

This module provides a centralized logging infrastructure with structured output, configurable log levels via environment variables, and a logger registry to avoid duplicate handlers. It wraps Python's standard `logging` module with project-specific defaults and dict-based message formatting.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Code                         │
│                                                             │
│    logger = create_logger(__name__)                         │
│    logger.info("Processing request", extra={...})           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  create_logger(name)                        │
│  - Check logger registry for existing logger                │
│  - Create CustomLogger if not found                         │
│  - Cache in registry and return                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    CustomLogger                             │
│  - Extends logging.Logger                                   │
│  - Configures from OS environment (LOG_LEVEL)               │
│  - Routes through log_to_dict() for structured output       │
│  - Outputs to stdout via StreamHandler                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   log_to_dict()                             │
│  - Converts message and args to dict format                 │
│  - Adds level prefix                                        │
│  - Passes through to underlying logger method               │
└─────────────────────────────────────────────────────────────┘
```

## File Structure

| File | Description |
|------|-------------|
| `__init__.py` | Exports `create_logger`, `CustomLogger`, `LogLevel` |
| `logging.py` | Core implementation: logger, config loading, formatters |

## Key Components

### LogLevel Enum

Maps standard Python log levels:

| Level | Value |
|-------|-------|
| `DEBUG` | 10 |
| `INFO` | 20 |
| `WARNING` | 30 |
| `ERROR` | 40 |
| `CRITICAL` | 50 |

### Environment Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Console log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | `DEBUG` |
| `ENVIRONMENT_SECRET_NAME` | Environment identifier for log context | `local/address-microservice` |

### CustomLogger

Extends `logging.Logger` with:
- Automatic configuration from environment
- Dict-based message formatting via `log_to_dict()`
- Console handler with timestamp format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

### Logger Registry

The `loggers` dict caches logger instances by name to:
- Prevent duplicate handler attachment
- Enable consistent configuration across modules
- Support fast logger retrieval

## Usage Example

```python
from http_py.logging import create_logger

logger = create_logger(__name__)

# Basic logging
logger.info("Server started")
logger.debug("Processing request", extra={"request_id": "abc123"})
logger.error("Database connection failed", exc_info=True)

# With structured data
logger.info({
    "event": "user_login",
    "user_id": 123,
    "ip": "192.168.1.1"
})
```

## Output Format

```
2026-02-16 12:34:56,789 - myapp.services - INFO - {'level': 'info:', 'message': 'Processing request'}
```

## Design Principles

1. **Single Source of Truth**: One logger per module name via registry
2. **Environment-Driven Config**: Log level from `LOG_LEVEL` env var
3. **Structured Output**: Dict-based messages for parseability
4. **Standard Library Foundation**: Extends `logging.Logger`, not replaces it

## Known Limitations

1. **Dict Conversion**: All messages are converted to dicts, which may lose standard `%`-style formatting
2. **No JSON Formatter**: Output is dict repr, not proper JSON
3. **No Context Propagation**: No built-in correlation ID / request context support
4. **Single Handler**: Only stdout, no file or remote handlers
5. **No Log Rotation**: Would need external tools for log management

### Migration Notes

When enhancing the logging module:
1. Maintain backward compatibility with `create_logger(__name__)` pattern
2. Make JSON formatting opt-in via environment variable
3. Context injection should be transparent to existing log calls
4. Consider structured logging libraries (structlog) for major refactors
