from fastapi import status, Request
from fastapi.responses import Response, StreamingResponse
from starlette.concurrency import iterate_in_threadpool

from shared.context import build_context
from modules.logging.logging import create_logger
from shared.environment import env
from shared.rate_limiter.types import RateLimitException
from shared.rate_limiter.services import (
    track_request,
    assert_capacity,
    TrackRequestArgs,
)


logger = create_logger(__name__)


async def rate_limiter_middleware(request: Request, call_next):  # type: ignore
    if env().DISABLE_RATE_LIMITER:
        return await call_next(request)
    path = request.url.path
    ctx = await build_context(request)

    try:
        await assert_capacity(path, ctx)
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

    request_body = None
    request_headers = None
    if env().DEBUG:
        request_headers = str(request.headers)
        request_body = (await request.body()).decode("utf-8")

    try:
        response: StreamingResponse = await call_next(request)
    except Exception as err:
        args = TrackRequestArgs(
            ctx=ctx,
            path=path,
            request_headers=request_headers,
            request_body=request_body,
            response_headers=None,
            response_body=None,
        )
        await track_request(args)
        raise err

    response_headers = None
    response_body: str | None = None
    if env().DEBUG:
        response_headers = str(response.headers)
        body = [chunk async for chunk in response.body_iterator]
        # We set this because if we don't, the response body will be empty
        response.body_iterator = iterate_in_threadpool(iter(body))
        if len(body) > 0:
            for chunk in body:
                response_body = chunk.decode()
                break
        else:
            response_body = ""
            logger.error("rate_limiter_middleware:UnexpectedEmptyBody")

    args = TrackRequestArgs(
        ctx=ctx,
        path=path,
        request_headers=request_headers,
        request_body=request_body,
        response_headers=response_headers,
        response_body=response_body,
    )
    await track_request(args)
    return response


def create_rate_limiter_middleware(path_whitelist: list[str]):  # type: ignore
    async def func(request: Request, call_next):  # type: ignore
        path = request.url.path
        if path in path_whitelist:
            return await call_next(request)
        return await rate_limiter_middleware(request, call_next)

    return func
