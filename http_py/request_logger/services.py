from typing import cast
import time

from starlette import status
from starlette.types import ASGIApp
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from http_py.context import ContextFactory
from http_py.requests.services import (
    StreamingResponse,
    extract_request_data,
    validate_request_data,
)
from http_py.logging.services import create_logger
from http_py.request_logger.types import RequestArgs
from http_py.request_logger.utils import save_request


logger = create_logger(__name__)


async def database_request_logger_middleware(
    path_whitelist: list[str],
    request: Request,
    call_next: RequestResponseEndpoint,
    create_service_context: ContextFactory,
) -> Response:
    path = request.url.path
    if path in path_whitelist:
        response: Response = await call_next(request)
        return response

    ctx = create_service_context(request)
    req_data = await extract_request_data(request)
    try:
        validate_request_data(req_data)
    except ValueError as err:
        logger.error(f"database_request_logger_middleware: {err}")
        return JSONResponse (status_code=400, content={"error": str(err)}) 
        
    response_headers: str | None = None
    response_body: str | None = None

    try:
        response = await call_next(request)
    except Exception as err:
        args = RequestArgs(
            ctx=ctx,
            path=req_data.path,
            from_cache=False,
            product_name=req_data.product_name,
            product_module=req_data.product_module,
            product_feature=req_data.product_feature,
            product_tenant=req_data.product_tenant,
            request_headers=req_data.request_headers,
            request_body=req_data.request_body,
            response_headers=response_headers,
            response_body=response_body,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        await save_request(args)
        raise err

    response_headers = str(response.headers)
    streaming_response = cast(StreamingResponse, response)
    body = [chunk async for chunk in streaming_response.body_iterator]
    streaming_response.body_iterator = iterate_in_threadpool(iter(body))
    if len(body) > 0:
        for chunk in body:
            response_body = chunk.decode()
            break
    else:
        response_body = ""
        logger.error("request_logger_middleware:UnexpectedEmptyBody")

    args = RequestArgs(
        ctx=ctx,
        path=req_data.path,
        from_cache=False,
        product_name=req_data.product_name,
        product_module=req_data.product_module,
        product_feature=req_data.product_feature,
        product_tenant=req_data.product_tenant,
        request_headers=req_data.request_headers,
        request_body=req_data.request_body,
        response_headers=response_headers,
        response_body=response_body,
        status_code=response.status_code,
    )
    await save_request(args)
    return response


class ConsoleRequestLoggerMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, path_whitelist: list[str] | None = None):
        super().__init__(app)
        self.path_whitelist = path_whitelist or []

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        if path in self.path_whitelist:
            response: Response = await call_next(request)
            return response

        start_time = time.perf_counter()
        response = await call_next(request)
        response_time = time.perf_counter() - start_time
        message = f"{request.method} {request.url.path} \
            {response.status_code} {response_time:.3f}s"
        logger.info(message)
        return response
    
class DatabaseRequestLoggerMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        path_whitelist: list[str],
        create_service_context: ContextFactory,
    ):
        super().__init__(app)
        self.path_whitelist = path_whitelist
        self.create_service_context = create_service_context

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        return await database_request_logger_middleware(
            self.path_whitelist, request, call_next, self.create_service_context
        )
    