from collections.abc import Callable

from starlette import status
from starlette.responses import Response

from http_py.context import ContextFactory
from http_py.request import Request, NextCallable, extract_request_data
from http_py.logging.logging import create_logger
from http_py.rate_limiter.types import RateLimitException
from http_py.rate_limiter.utils import assert_capacity


logger = create_logger(__name__)


async def rate_limiter_middleware(
    path_whitelist: list[str],
    request: Request,
    call_next: NextCallable,
    create_service_context: ContextFactory,
):
    path = request.url.path
    if path in path_whitelist:
        return await call_next(request)

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
        return Response(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=f"{detail} - BODY:{request_body} - HEADERS:{headers}",
        )

    return await call_next(request)


def create_rate_limiter_middleware(
    path_whitelist: list[str], create_service_context: ContextFactory
) -> Callable:
    async def func(request: Request, call_next: NextCallable):
        return await rate_limiter_middleware(
            path_whitelist, request, call_next, create_service_context
        )

    return func
