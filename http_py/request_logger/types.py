from typing import NamedTuple
from dataclasses import dataclass

from http_py.context import ContextProtocol


# Only fields that can be overridden
class RequestLoggerOverride(NamedTuple):
    product_name: str | None = None
    product_module: str | None = None
    product_feature: str | None = None
    product_tenant: str | None = None
    request_headers: str | None = None
    request_body: str | None = None


@dataclass(frozen=True)
class RequestArgs:
    ctx: ContextProtocol
    path: str
    from_cache: bool
    product_name: str | None
    product_module: str | None
    product_feature: str | None
    product_tenant: str | None
    request_headers: str | None
    request_body: str | None
    response_headers: str | None
    response_body: str | None
    status_code: int | None = None
    duration_ms: int | None = None
    request_uuid: str | None = None
