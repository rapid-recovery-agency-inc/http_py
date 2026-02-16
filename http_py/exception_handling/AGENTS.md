# Exception Handling Module

## Purpose

This module provides a declarative factory for building unified FastAPI exception handlers. It produces a single async handler from a name→rule mapping, enabling consistent error responses, structured logging, and customizable content builders across all exception types.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Exception Raised                         │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              create_exception_handler()                     │
│  - Builds unified handler from HandlerRule mapping          │
│  - Returns async callable for FastAPI registration          │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                     handler()                               │
│  - Extracts request metadata (request_id, path, method)     │
│  - Matches exception via isinstance against rules           │
│  - Invokes content_builder or uses default detail           │
│  - Logs with structured extras and exc_info                 │
│  - Returns JSONResponse with status_code                    │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Content Builders                           │
│  - build_validation_content: Pydantic errors + request body │
│  - build_client_error_content: AWS ClientError metadata     │
│  - build_unexpected_content: Exception type for debugging   │
└─────────────────────────────────────────────────────────────┘
```

## File Structure

| File | Description |
|------|-------------|
| `__init__.py` | Exports public API: handlers, rules, and content builders |
| `services.py` | `create_exception_handler()` factory and `get_request_metadata()` |
| `types.py` | `HandlerRule` NamedTuple, `ContentBuilderFn` type alias, `FastAPIRequestValidationError` protocol |
| `utils.py` | Pre-built content builders for common exception types |

## Key Types

### HandlerRule

Declarative rule mapping an exception type to a response shape:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `exc_type` | `type[Exception]` | required | Exception class to match via isinstance |
| `status_code` | `int` | required | HTTP status code for the response |
| `log_level` | `Literal[...]` | `"error"` | Logger method name; `None` to suppress logging |
| `include_detail` | `bool` | `True` | Include `str(exc)` in response when no content_builder |
| `content_builder` | `ContentBuilderFn` | `None` | Async callback for custom response content |

### ContentBuilderFn

```python
Callable[
    [Request, Exception, dict[str, str]],
    Awaitable[tuple[dict[str, Any] | None, dict[str, Any]]]
]
```

Receives request, exception, and metadata dict. Returns tuple of (response_content, log_extras).

## Usage Example

```python
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from botocore.exceptions import ClientError

from http_py.exception_handling import (
    create_exception_handler,
    HandlerRule,
    build_validation_content,
    build_client_error_content,
    build_unexpected_content,
)

HANDLER_MAP = {
    "validation": HandlerRule(
        exc_type=RequestValidationError,
        status_code=422,
        log_level="warning",
        content_builder=build_validation_content,
    ),
    "aws_client": HandlerRule(
        exc_type=ClientError,
        status_code=502,
        log_level="error",
        content_builder=build_client_error_content,
    ),
    "catch_all": HandlerRule(
        exc_type=Exception,
        status_code=500,
        log_level="error",
        content_builder=build_unexpected_content,
    ),
}

app = FastAPI()
app.add_exception_handler(Exception, create_exception_handler(HANDLER_MAP))
```

## Design Principles

1. **Declarative Configuration**: Exception handling behavior is defined via data structures, not scattered try/except blocks
2. **Consistent Response Shape**: All errors include `request_id`, `path`, and `method` for traceability
3. **Structured Logging**: Every exception is logged with request context and optional custom extras
4. **Extensibility**: Custom content builders allow project-specific response shapes without modifying core logic
5. **Zero Project-Specific Imports**: Only depends on Starlette and stdlib

## Future Enhancements

### Planned Features

- [ ] **Exception Metrics**: Integration with Prometheus/StatsD for error rate tracking
- [ ] **Retry Hints**: Add `Retry-After` header support for rate-limited or temporary failures
- [ ] **Error Codes**: Standardized error code taxonomy for client SDK consumption
- [ ] **Response Serialization**: Support for non-JSON responses (XML, Protocol Buffers)
- [ ] **Circuit Breaker Integration**: Automatic error counting for downstream service failures
- [ ] **Sentry/Datadog Integration**: Built-in hooks for APM error reporting
- [ ] **Request Replay**: Capture enough context to replay failed requests in testing

### Extension Points

1. **Custom Content Builders**: Implement `ContentBuilderFn` for domain-specific error shapes
2. **Log Level Override**: Environment-based suppression of specific exception types
3. **Response Transformers**: Post-processing hooks for response modification
4. **Error Aggregation**: Batch multiple validation errors into single response

### Migration Notes

When adding new exception types:
1. Define a `HandlerRule` with appropriate `exc_type` and `status_code`
2. Create a content builder if custom response shape is needed
3. Add rule to handler map **before** the catch-all `Exception` rule
4. Rules are evaluated in insertion order; first match wins
