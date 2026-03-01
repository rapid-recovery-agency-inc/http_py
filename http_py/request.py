import json
from typing import Any, Protocol
from dataclasses import dataclass
from collections.abc import Callable, Awaitable

from http_py.logging.services import create_logger


logger = create_logger(__name__)


class Url(Protocol):
    path: str


class QueryParams(Protocol):
    def get(
        self,
        key: str,
    ) -> str | None: ...

    def keys(self) -> list[str]: ...

    def __getitem__(self, key: str) -> str: ...


class Headers(Protocol):
    def __str__(self) -> str: ...
    def get(self, key: str, default: str | None = None) -> str | None: ...


class Request(Protocol):
    url: Url
    headers: Headers
    method: str
    query_params: QueryParams
    state: object

    async def body(self) -> bytes: ...


class StreamingResponse(Protocol):
    headers: Headers
    body_iterator: Any  # Should be an async iterator yielding bytes


class Response(Protocol):
    status_code: int
    body: bytes | memoryview


NextCallable = Callable[[Request], Awaitable[Response]]
StreamingNextCallable = Callable[[Request], Awaitable[StreamingResponse]]


@dataclass(frozen=True)
class ExtractedRequestData:
    path: str
    request_headers: str
    request_body: str
    product_name: str | None
    product_module: str | None
    product_feature: str | None
    product_tenant: str | None


async def extract_request_data(request: Request) -> ExtractedRequestData:
    """Extract path, headers, body, and product fields from a request.

    For POST requests, product fields are extracted from the JSON body.
    For GET requests, product fields are extracted from query parameters.

    Args:
        request: The incoming request object.

    Returns:
        ExtractedRequestData containing all extracted fields.
    """
    path = request.url.path
    request_body = (await request.body()).decode("utf-8")
    request_headers = str(request.headers)

    product_name: str | None = None
    product_module: str | None = None
    product_feature: str | None = None
    product_tenant: str | None = None

    if request.method == "POST" and request_body:
        try:
            body_json = json.loads(request_body)
            product_name = body_json.get("product_name")
            product_module = body_json.get("product_module")
            product_feature = body_json.get("product_feature")
            product_tenant = body_json.get("product_tenant")
        except json.JSONDecodeError:
            logger.exception(
                "extract_request_data: Failed to decode JSON body", exc_info=True
            )
            raise
    elif request.method == "GET":
        product_name = request.query_params.get("product_name")
        product_module = request.query_params.get("product_module")
        product_feature = request.query_params.get("product_feature")
        product_tenant = request.query_params.get("product_tenant")

    return ExtractedRequestData(
        path=path,
        request_headers=request_headers,
        request_body=request_body,
        product_name=product_name,
        product_module=product_module,
        product_feature=product_feature,
        product_tenant=product_tenant,
    )
