from http import HTTPStatus
from collections.abc import Callable, Awaitable

from starlette.requests import Request
from starlette.responses import Response as StarletteResponse

from http_py.context import ContextFactory
from http_py.request import Response, NextCallable, extract_request_data
from http_py.logging.services import create_logger
from http_py.rate_limiter.types import RateLimitException
from http_py.rate_limiter.utils import assert_capacity


logger = create_logger(__name__)


async def rate_limiter_middleware(
    path_whitelist: list[str],
    request: Request,
    call_next: NextCallable,
    create_service_context: ContextFactory,
) -> Response:
    path = request.url.path
    if path in path_whitelist:
        response: Response = await call_next(request)
        return response

    ctx = await create_service_context(request)
    req_data = await extract_request_data(request)
    try:
        await assert_capacity(req_data, ctx)
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


def create_rate_limiter_middleware(
    path_whitelist: list[str], create_service_context: ContextFactory
) -> Callable[[Request, NextCallable], Awaitable[Response]]:
    async def func(request: Request, call_next: NextCallable) -> Response:
        return await rate_limiter_middleware(
            path_whitelist, request, call_next, create_service_context
        )

    return func
