import hmac
from typing import Any
from urllib.parse import quote as urlquote, urlparse, ParseResult


def sign(
    secret_key: str,
    url: str,
    params: dict[str, Any] | None = None,
    body: bytes | None = None,
) -> str:
    """Generate HMAC-SHA256 signature for a request.

    Args:
        secret_key: The secret key for HMAC signing.
        url: The full request URL.
        params: Query parameters dict.
        body: Request body bytes (for POST requests).

    Returns:
        Hex-encoded HMAC-SHA256 signature.
    """
    parsed_url: ParseResult = urlparse(url)
    path_: str = urlquote(parsed_url.path, safe="/:")

    # Sort and append keys and values into a single string
    sorted_params_: str = (
        "".join(f"{key}{value}" for key, value in sorted(params.items()))
        if params
        else ""
    )

    # Directly encode body as string
    body_: str = body.decode("utf-8") if body else ""

    # Build message
    message: str = f"{path_.strip()}{sorted_params_.strip()}{body_.strip()}"

    # Calculate the HMAC signature
    message_bytes = message.encode("utf-8")
    signature = hmac.new(
        secret_key.encode("utf-8"),
        message_bytes,
        digestmod="sha256",
    ).hexdigest()

    return signature
