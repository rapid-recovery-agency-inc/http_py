import hmac

from fastapi import Request, HTTPException

from http_py.hmac import HmacSigner
from shared.strings import (
    HMAC_INVALID_SIGNATURE,
    HMAC_MISSING_SIGNATURE,
    HMAC_UNSUPPORTED_METHOD,
)
from http_py.environment.environment import env


async def require_hmac_signature(request: Request) -> None:
    """Check for the HMAC signature in the request header and verify it.

    Validates the HMAC signature of the incoming request, including
    its body if POST, against the provided signature using secret keys
    stored in the configuration. Raises an HTTPException if the signature
    is missing, invalid, or if the request method is not supported.

    Args:
    ----
        request (Request): The FastAPI request object.

    Raises:
    ------
        HTTPException: If signature is missing, invalid, or if method is not supported.

    """
    if env().DISABLE_HMAC:
        return

    # Get the HMAC signature from the request header
    header_name: str = env().HMAC_SIGNATURE_HEADER_NAME
    signature: str | None = request.headers.get(header_name, None)

    if signature is None:
        raise HTTPException(status_code=401, detail=HMAC_MISSING_SIGNATURE)

    if request.method not in ["GET", "POST"]:
        raise HTTPException(status_code=401, detail=HMAC_UNSUPPORTED_METHOD)

    # Extract necessary components from the request
    params: dict[str, str] = dict(request.query_params)
    body: bytes | None = await request.body() if request.method == "POST" else None

    # Validate the signature
    is_valid_signature: bool = False
    for secret in env().SECRETS:
        if isinstance(secret, SecretStr):
            secret = secret.get_secret_value()  # noqa: PLW2901
        auth_signer: HmacSigner = HmacSigner(secret)
        expected_signature: str = await auth_signer.sign(str(request.url), params, body)

        # Early ending on first valid signature
        if hmac.compare_digest(expected_signature, signature):
            is_valid_signature = True
            break

    # Raise an exception if the signature is invalid
    if not is_valid_signature:
        raise HTTPException(status_code=401, detail=HMAC_INVALID_SIGNATURE)
