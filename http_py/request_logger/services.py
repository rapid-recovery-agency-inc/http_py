from collections.abc import Callable

# TODO: Consider decoupling starlette framework
from starlette.responses import StreamingResponse
from starlette.concurrency import iterate_in_threadpool

from http_py.context import ContextFactory
from http_py.request import Request, NextCallable, extract_request_data
from http_py.logging.logging import create_logger
from http_py.request_logger.types import RequestArgs
from http_py.request_logger.utils import save_request


logger = create_logger(__name__)


async def request_logger_middleware(
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
    response_headers: str | None = None
    response_body: str | None = None

    try:
        response: StreamingResponse = await call_next(request)
    except Exception as err:
        args = RequestArgs(
            ctx=ctx,
            path=req_data.path,
            product_name=req_data.product_name,
            product_module=req_data.product_module,
            product_feature=req_data.product_feature,
            product_tenant=req_data.product_tenant,
            request_headers=req_data.request_headers,
            request_body=req_data.request_body,
            response_headers=response_headers,
            response_body=response_body,
        )
        await save_request(args)
        raise err

    response_headers = str(response.headers)
    body = [chunk async for chunk in response.body_iterator]
    response.body_iterator = iterate_in_threadpool(iter(body))
    if len(body) > 0:
        for chunk in body:
            response_body = chunk.decode()
            break
    else:
        response_body = ""
        logger.error("rate_limiter_middleware:UnexpectedEmptyBody")

    args = RequestArgs(
        ctx=ctx,
        path=req_data.path,
        product_name=req_data.product_name,
        product_module=req_data.product_module,
        product_feature=req_data.product_feature,
        product_tenant=req_data.product_tenant,
        request_headers=req_data.request_headers,
        request_body=req_data.request_body,
        response_headers=response_headers,
        response_body=response_body,
    )
    await save_request(args)
    return response


def create_request_logger_middleware(
    path_whitelist: list[str], create_service_context: ContextFactory
) -> Callable:
    async def func(
        request: Request,
        call_next: NextCallable,
    ):
        return await request_logger_middleware(
            path_whitelist, request, call_next, create_service_context
        )

    return func
