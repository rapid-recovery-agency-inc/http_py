import time
import uuid
from typing import cast

from starlette import status
from starlette.types import ASGIApp
from starlette.requests import Request
from starlette.responses import Response, JSONResponse, StreamingResponse
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from http_py.context import ContextFactory
from http_py.logging.services import create_logger
from http_py.requests.services import (
    extract_request_data,
    validate_request_data,
)
from http_py.request_logger.types import RequestArgs, RequestLoggerOverride
from http_py.request_logger.utils import save_request


logger = create_logger(__name__)


async def database_request_logger_middleware(
    path_whitelist: list[str],
    request: Request,
    call_next: RequestResponseEndpoint,
    create_service_context: ContextFactory,
    override: RequestLoggerOverride | None = None,
) -> Response:
    path = request.url.path
    if path in path_whitelist:
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = str(uuid.uuid4())
        return response

    request_uuid = str(uuid.uuid4())

    ctx = create_service_context(request)

    req_data = await extract_request_data(request)
    # Merge overrides into req_data dict if provided
    req_data_dict = req_data.__dict__.copy()
    if override:
        for field in RequestLoggerOverride._fields:
            value = getattr(override, field, None)
            if value is not None:
                req_data_dict[field] = value
    try:
        validate_request_data(type(req_data)(**req_data_dict))
    except ValueError as err:
        logger.error(f"database_request_logger_middleware: {err}")
        error_response = JSONResponse(status_code=400, content={"error": str(err)})
        error_response.headers["X-Request-ID"] = request_uuid
        return error_response

    response_headers: str | None = None
    response_body: str | None = None

    start_time = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as err:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        args = RequestArgs(
            ctx=ctx,
            path=req_data_dict["path"],
            from_cache=False,
            product_name=req_data_dict.get("product_name"),
            product_module=req_data_dict.get("product_module"),
            product_feature=req_data_dict.get("product_feature"),
            product_tenant=req_data_dict.get("product_tenant"),
            request_headers=req_data_dict.get("request_headers"),
            request_body=req_data_dict.get("request_body"),
            response_headers=response_headers,
            response_body=response_body,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            duration_ms=duration_ms,
            request_uuid=request_uuid,
        )
        await save_request(args)
        raise err

    response.headers["X-Request-ID"] = request_uuid
    response_headers = str(response.headers)
    streaming_response = cast(StreamingResponse, response)
    body = [chunk async for chunk in streaming_response.body_iterator]
    streaming_response.body_iterator = iterate_in_threadpool(iter(body))
    if len(body) > 0:
        for chunk in body:
            response_body = chunk.decode()  # type: ignore
            break
    else:
        response_body = ""
        logger.error("request_logger_middleware:UnexpectedEmptyBody")

    duration_ms = int((time.perf_counter() - start_time) * 1000)
    args = RequestArgs(
        ctx=ctx,
        path=req_data_dict["path"],
        from_cache=False,
        product_name=req_data_dict.get("product_name"),
        product_module=req_data_dict.get("product_module"),
        product_feature=req_data_dict.get("product_feature"),
        product_tenant=req_data_dict.get("product_tenant"),
        request_headers=req_data_dict.get("request_headers"),
        request_body=req_data_dict.get("request_body"),
        response_headers=response_headers,
        response_body=response_body,
        status_code=response.status_code,
        duration_ms=duration_ms,
        request_uuid=request_uuid,
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
        override: RequestLoggerOverride | None = None,
    ):
        super().__init__(app)
        self.path_whitelist = path_whitelist
        self.create_service_context = create_service_context
        self.override = override

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        return await database_request_logger_middleware(
            self.path_whitelist,
            request,
            call_next,
            self.create_service_context,
            self.override,
        )
