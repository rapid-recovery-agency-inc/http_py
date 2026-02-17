"""Examples: http_py.hmac module usage.

This example demonstrates HMAC-SHA256 signature verification
for secure API request validation using the http_py library.
"""

from dataclasses import dataclass

from http_py.hmac import (
    sign,
)


# ──────────────────────────────────────────────────────────────────────
# 1. Environment Configuration (implements HMACEnvironment protocol)
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class HMACEnv:
    """HMAC configuration implementing HMACEnvironment protocol."""

    SECRETS: list[str]  # Multiple secrets for key rotation
    HMAC_HEADER_NAME: str = "X-HMAC-Signature"


# ──────────────────────────────────────────────────────────────────────
# 2. Signing Requests (Client Side)
# ──────────────────────────────────────────────────────────────────────


def create_signed_request_example() -> None:
    """Create HMAC signature for outbound requests."""
    secret = "my_secret_key"

    # Sign a GET request
    get_signature = sign(
        secret_key=secret,
        url="https://api.example.com/users",
        params={"page": "1", "limit": "10"},
        body=None,
    )
    # -> hex digest to send in header

    # Sign a POST request with body
    post_signature = sign(
        secret_key=secret,
        url="https://api.example.com/users",
        params=None,
        body=b'{"name": "Alice", "email": "alice@example.com"}',
    )


# ──────────────────────────────────────────────────────────────────────
# 3. Verifying Requests (Server Side with FastAPI)
# ──────────────────────────────────────────────────────────────────────


# FastAPI dependency example:
#
# from fastapi import FastAPI, Request, Depends
# from http_py.hmac import require_hmac_signature, HMACException
#
# app = FastAPI()
#
# env = HMACEnv(
#     SECRETS=["current_secret", "previous_secret"],  # Key rotation
#     HMAC_HEADER_NAME="X-HMAC-Signature",
# )
#
# async def verify_hmac(request: Request):
#     '''Dependency to verify HMAC signature.'''
#     await require_hmac_signature(request, env)
#
# @app.post("/secure/endpoint", dependencies=[Depends(verify_hmac)])
# async def secure_endpoint():
#     return {"status": "authorized"}
#
# @app.exception_handler(HMACException)
# async def handle_hmac_error(request: Request, exc: HMACException):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"error": exc.detail}
#     )


# ──────────────────────────────────────────────────────────────────────
# 4. Key Rotation Support
# ──────────────────────────────────────────────────────────────────────


def key_rotation_example() -> None:
    """Support multiple secrets for seamless key rotation.

    The library tries each secret until one validates.
    """
    env = HMACEnv(
        SECRETS=[
            "new_secret_2024",  # Current secret
            "old_secret_2023",  # Previous secret (for transition period)
        ],
        HMAC_HEADER_NAME="X-HMAC-Signature",
    )
    # Both old and new signed requests will validate during rotation


# ──────────────────────────────────────────────────────────────────────
# 5. Manual Signature Verification
# ──────────────────────────────────────────────────────────────────────


def manual_verification_example() -> None:
    """Manually verify signatures without FastAPI."""
    import hmac as hmac_stdlib

    secret = "my_secret"
    url = "https://api.example.com/data"
    params = {"id": "123"}
    body = None

    # Generate expected signature
    expected = sign(secret, url, params, body)

    # Compare with incoming signature (use compare_digest!)
    incoming_signature = "abc123..."  # From request header
    is_valid = hmac_stdlib.compare_digest(expected, incoming_signature)
