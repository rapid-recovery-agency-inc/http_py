from dataclasses import dataclass

from http_py.context import ContextProtocol


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
