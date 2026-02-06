import hmac
from typing import Any
from urllib.parse import quote as urlquote, urlparse, ParseResult


class HmacSigner:
    """Class for generating HMAC signatures for API requests.

    This class provides a method to generate HMAC signatures using a given secret key.
    """

    def __init__(self, secret_key: str):
        """Initializes HmacAuthSigner with a secret key.

        Args:
        ----
            secret_key (str): The secret key as a string.

        """
        self.secret_key: bytes = secret_key.encode("utf-8")

    async def sign(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        body: bytes | None = None,
    ) -> str:
        """Generates HMAC signature for given request without including HTTP method.

        Notes:
        -----
            GET:
                <url_path><optional sorted params string>
            POST:
                <url_path><optional sorted params string><optional body string as is>

        Args:
        ----
            url: The URL of the request.
            params: The query parameters for the request, if any.
            body: The raw byte string body of the request for POST, if any.

        Returns:
        -------
            The generated HMAC signature as a hexadecimal string.

        """
        # Quote base url
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
            self.secret_key,
            message_bytes,
            digestmod="sha256",
        ).hexdigest()

        return signature
