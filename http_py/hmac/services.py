import hmac
from collections.abc import Callable, Awaitable

from http_py.types import HMACEnvironment
from http_py.request import Request
from http_py.hmac.utils import sign
from http_py.hmac.constants import (
    HMAC_INVALID_SIGNATURE,
    HMAC_MISSING_SIGNATURE,
    HMAC_UNSUPPORTED_METHOD,
)
from http_py.hmac.exceptions import HMACException


DEFAULT_HEADER_NAME: str = "RRA-HMAC-Signature"


async def require_hmac_signature(request: Request, env: HMACEnvironment) -> None:
    signature: str | None = request.headers.get(env.HMAC_HEADER_NAME, None)

    if signature is None:
        raise HMACException(status_code=401, detail=HMAC_MISSING_SIGNATURE)

    if request.method not in ["GET", "POST"]:
        raise HMACException(status_code=401, detail=HMAC_UNSUPPORTED_METHOD)

    # Extract necessary components from the request
    params: dict[str, str] = dict(request.query_params)
    body: bytes | None = await request.body() if request.method == "POST" else None

    # Validate the signature
    is_valid_signature: bool = False
    for secret in env.SECRETS:
        expected_signature: str = sign(secret, str(request.url), params, body)

        # Early ending on first valid signature
        if hmac.compare_digest(expected_signature, signature):
            is_valid_signature = True
            break

    # Raise an exception if the signature is invalid
    if not is_valid_signature:
        raise HMACException(status_code=401, detail=HMAC_INVALID_SIGNATURE)


async def hmac_dependency_factory(
    env: HMACEnvironment,
) -> Callable[[Request], Awaitable[None]]:
    async def dependency(request: Request) -> None:
        await require_hmac_signature(request, env)

    return dependency
