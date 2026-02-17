# HMAC Module

## Purpose

This module provides HMAC-SHA256 signature verification for HTTP API authentication. It enables request signing and validation to ensure requests originate from trusted clients with shared secrets.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Incoming Request                         │
│  Headers: { "RRA-HMAC-Signature": "abc123..." }             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│            require_hmac_signature(request, env)             │
│  1. Extract signature from header (env.HMAC_HEADER_NAME)    │
│  2. Validate HTTP method (GET, POST only)                   │
│  3. Extract URL, params, body from request                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              For each secret in env.SECRETS                 │
│  - Generate expected signature: sign(secret, url, params)   │
│  - Compare with request signature (timing-safe)             │
│  - Break on first match                                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
┌───────────────┐           ┌───────────────┐
│   Valid       │           │   Invalid     │
│   Continue    │           │  HMACException│
│   to handler  │           │  (401)        │
└───────────────┘           └───────────────┘
```

## File Structure

| File | Description |
|------|-------------|
| `__init__.py` | Exports public API |
| `constants.py` | Error message constants |
| `exceptions.py` | `HMACException` for authentication failures |
| `services.py` | `require_hmac_signature()` validation function |
| `utils.py` | `sign()` function for generating HMAC signatures |

## Key Components

### sign(secret_key, url, params, body) → str

Generates HMAC-SHA256 signature from request components:

1. Parse and URL-encode the path
2. Sort and concatenate query parameters
3. Decode body as UTF-8
4. Build message: `{path}{sorted_params}{body}`
5. Return hex-encoded HMAC-SHA256

### require_hmac_signature(request, env)

Validates incoming request signature:

1. Extract signature from configured header
2. Reject non-GET/POST methods
3. Try each secret in `env.SECRETS` (supports key rotation)
4. Use `hmac.compare_digest()` for timing-safe comparison
5. Raise `HMACException(401)` on failure

### HMACException

Custom exception with HTTP semantics:

| Attribute | Type | Description |
|-----------|------|-------------|
| `status_code` | int | HTTP status (typically 401) |
| `detail` | Any | Error message |
| `headers` | dict | Optional response headers |

## Environment Configuration

Requires `HMACEnvironment` protocol from `http_py.types`:

| Field | Type | Description |
|-------|------|-------------|
| `SECRETS` | list[str] | List of valid signing secrets (for rotation) |
| `HMAC_HEADER_NAME` | str | Header name containing signature |

## Usage Example

### Server-Side (Validation)

```python
from starlette.requests import Request
from http_py.hmac import require_hmac_signature, HMACException

@dataclass(frozen=True)
class AppEnv:
    SECRETS: list[str] = field(default_factory=lambda: ["secret1", "secret2"])
    HMAC_HEADER_NAME: str = "X-HMAC-Signature"

async def protected_endpoint(request: Request):
    env = AppEnv()
    try:
        await require_hmac_signature(request, env)
    except HMACException as e:
        return JSONResponse({"error": e.detail}, status_code=e.status_code)
    
    # Process authenticated request
    return JSONResponse({"status": "ok"})
```

### Client-Side (Signing)

```python
import httpx
from http_py.hmac import sign

def make_signed_request(url: str, secret: str, params: dict = None):
    signature = sign(secret, url, params)
    headers = {"X-HMAC-Signature": signature}
    
    response = httpx.get(url, params=params, headers=headers)
    return response
```

## Signature Algorithm

```
message = url_encode(path) + sort_concat(params) + body
signature = hmac_sha256(secret, message).hexdigest()
```

Example:
```
URL: https://api.example.com/users?name=alice&age=30
Body: {"action": "create"}

path = "/users"
sorted_params = "age30namealice"  # sorted by key
body = '{"action": "create"}'

message = "/usersage30namealice{\"action\": \"create\"}"
signature = hmac_sha256("secret", message) → "a1b2c3..."
```

## Design Principles

1. **Multiple Secrets**: Supports key rotation without downtime
2. **Timing-Safe Comparison**: Uses `hmac.compare_digest()` to prevent timing attacks
3. **Method Restriction**: Only GET and POST supported (extend as needed)
4. **Configurable Header**: Header name from environment, not hardcoded

## Known Limitations

1. **GET/POST Only**: Other HTTP methods (PUT, DELETE, PATCH) rejected
2. **No Timestamp**: Vulnerable to replay attacks without additional timestamp validation
3. **No Nonce**: No protection against duplicate requests
4. **Body Encoding**: Assumes UTF-8 body encoding

## Future Enhancements

### Planned Features

- [ ] **Timestamp Validation**: Reject requests older than N seconds
- [ ] **Nonce Support**: One-time use tokens to prevent replays
- [ ] **All HTTP Methods**: Support PUT, DELETE, PATCH
- [ ] **Algorithm Selection**: Support SHA-384, SHA-512
- [ ] **Middleware Factory**: Create Starlette middleware easily
- [ ] **Client SDK**: Helper class for signing outgoing requests
- [ ] **Request Logging**: Log signature validation attempts
- [ ] **Rate Limiting**: Per-client rate limits on failed validations

### Extension Points

1. **Custom Message Builder**: Override how the signing message is constructed
2. **Header Extractor**: Support multiple header formats or auth schemes
3. **Secret Provider**: Async secret fetching from vault/secret manager

### Example: Timestamp Validation (Future)

```python
import time

MAX_REQUEST_AGE_SECONDS = 300  # 5 minutes

async def require_hmac_with_timestamp(request: Request, env: HMACEnvironment):
    timestamp = request.headers.get("X-Request-Timestamp")
    if timestamp is None:
        raise HMACException(401, "Missing timestamp")
    
    request_time = int(timestamp)
    current_time = int(time.time())
    
    if abs(current_time - request_time) > MAX_REQUEST_AGE_SECONDS:
        raise HMACException(401, "Request expired")
    
    # Include timestamp in signature validation
    await require_hmac_signature(request, env)
```

### Migration Notes

When extending the HMAC module:
1. Maintain backward compatibility with existing signature format
2. Add new validation rules as opt-in via environment flags
3. Consider versioning signatures (e.g., `v1:signature`, `v2:signature`)
4. Update client SDKs when changing signature algorithm
