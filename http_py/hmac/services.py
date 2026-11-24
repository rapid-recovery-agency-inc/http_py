import hmac
import warnings

from http_py.types import HMACEnvironment
from http_py.hmac.types import HMACFactoryDependency
from http_py.hmac.utils import sign
from http_py.hmac.constants import (
    HMAC_INVALID_SIGNATURE,
    HMAC_MISSING_SIGNATURE,
    HMAC_UNSUPPORTED_METHOD,
)
from http_py.hmac.exceptions import HMACException
from http_py.requests.services import Request


DEFAULT_HEADER_NAME: str = "RRA-HMAC-Signature"


def resolve_signature_header_name(env: HMACEnvironment) -> str:
    """Resolve the request header that carries the HMAC signature.

    Precedence: HMAC_SIGNATURE_HEADER_NAME, then the legacy
    HMAC_HEADER_NAME, then DEFAULT_HEADER_NAME.
    """
    name: str | None = getattr(env, "HMAC_SIGNATURE_HEADER_NAME", None)
    if name and str(name).strip():
        return str(name)
    legacy_name: str | None = getattr(env, "HMAC_HEADER_NAME", None)
    if legacy_name and str(legacy_name).strip():
        warnings.warn(
            "HMAC_HEADER_NAME is deprecated; set HMAC_SIGNATURE_HEADER_NAME instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return str(legacy_name)
    return DEFAULT_HEADER_NAME


async def require_hmac_signature(request: Request, env: HMACEnvironment) -> None:
    signature: str | None = request.headers.get(
        resolve_signature_header_name(env), None
    )

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


def build_hmac_factory_dependency(
    env: HMACEnvironment,
) -> HMACFactoryDependency:
    if not env.SECRETS or not isinstance(env.SECRETS, list) or len(env.SECRETS) == 0:
        raise ValueError(
            "require_hmac_signature:SECRETS must be a non-empty list in the environment"
        )

    async def dependency(request: Request) -> None:
        await require_hmac_signature(request, env)

    return dependency
