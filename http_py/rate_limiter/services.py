from http import HTTPStatus

from starlette.types import ASGIApp
from starlette.requests import Request
from starlette.responses import Response, Response as StarletteResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from http_py.context import ContextFactory
from http_py.logging.services import create_logger
from http_py.requests.services import extract_request_data
from http_py.rate_limiter.types import RateLimitException
from http_py.rate_limiter.utils import assert_capacity
from http_py.rate_limiter.constants import RULE_CACHING_EXPIRATION_IN_SECONDS


logger = create_logger(__name__)


async def rate_limiter_middleware(  # noqa: PLR0913
    path_whitelist: list[str],
    request: Request,
    call_next: RequestResponseEndpoint,
    create_service_context: ContextFactory,
    rule_caching_expiration_seconds: int,
    table_prefix: str | None = None,
) -> Response:
    path = request.url.path
    if path in path_whitelist:
        response: Response = await call_next(request)
        return response

    ctx = create_service_context(request)
    req_data = await extract_request_data(request)
    try:
        await assert_capacity(
            req_data, ctx, rule_caching_expiration_seconds, table_prefix
        )
    except RateLimitException as err:
        request_body = (await request.body()).decode("utf-8")
        headers = str(request.headers)
        detail = f"{err.__class__.__name__}: {err!s}"
        logger.error(
            "rate_limiter_middleware:RateLimitException: detail=%r, request_body=%r",
            detail,
            request_body,
        )
        return StarletteResponse(
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
            content=f"{detail} - BODY:{request_body} - HEADERS:{headers}",
        )

    response = await call_next(request)
    return response


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        path_whitelist: list[str],
        create_service_context: ContextFactory,
        table_prefix: str | None = None,
        rule_caching_expiration_seconds: int = RULE_CACHING_EXPIRATION_IN_SECONDS,
    ):
        super().__init__(app)
        self.path_whitelist = path_whitelist
        self.create_service_context = create_service_context
        self.table_prefix = table_prefix
        self.rule_caching_expiration_seconds = rule_caching_expiration_seconds

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        return await rate_limiter_middleware(
            self.path_whitelist,
            request,
            call_next,
            self.create_service_context,
            self.rule_caching_expiration_seconds,
            self.table_prefix,
        )
