"""
Generic v2 router factory with rate limiter parameters.

Any service (Foundd, Insightt, etc.) can use this factory to create
a v2 router that enforces rate limiter parameters on every endpoint.

Usage:
    from http_py.routers import create_v2_router

    async def my_handler(request: Request, rate_limiter_params: RateLimiterParams)
    -> Response:
        # your logic here
        ...

    router = create_v2_router(
        handler=my_handler,
        tags=["v2"],
        heartbeat_extra={"service": "foundd"},
    )
    app.include_router(router, prefix="/v2")
"""

from enum import Enum
from typing import Any
from collections.abc import Callable, Awaitable

from fastapi import Query, status
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse
from starlette.requests import Request

from http_py.request import extract_request_data, ExtractedRequestData


V2Handler = Callable[[Request, ExtractedRequestData], Awaitable[JSONResponse]]


def create_v2_router(
    handler: V2Handler,
    *,
    tags: list[str | Enum] | None = None,
    heartbeat_extra: dict[str, Any] | None = None,
) -> APIRouter:
    """
    Create a generic v2 APIRouter with rate limiter params enforced.
    Uses ExtractedRequestData from http_py.request — already contains
    product_name, product_module, product_feature, product_tenant.

    Args:
        handler: Async function with signature:
        async (request, ExtractedRequestData) -> JSONResponse
        tags: FastAPI tags for OpenAPI docs (default: ["v2"])
        heartbeat_extra: Extra fields to include in the /heartbeat response.

    Returns:
    An APIRouter ready to be registered with app.include_router(...)
    """

    default_tags: list[str | Enum] = ["v2"]
    resolved_tags: list[str | Enum] | None = tags if tags is not None else default_tags
    router = APIRouter(tags=resolved_tags)

    @router.post("/", status_code=status.HTTP_200_OK)
    async def v2_endpoint(
        request: Request,
        product_name: str = Query(..., description="Product name, e.g. 'foundd'"),
        product_module: str = Query(..., description="Module, e.g. 'scoring'"),
        product_feature: str = Query(
            ..., description="Feature, e.g. 'calculate_hotspots'"
        ),
        product_tenant: str = Query(..., description="Client ID / tenant identifier"),
    ) -> JSONResponse:
        """V2 endpoint — extracts request data and delegates to service handler."""

        req_data = await extract_request_data(request)  # type: ignore [arg-type]

        return await handler(request, req_data)

    @router.post("/heartbeat", status_code=status.HTTP_200_OK)
    async def v2_heartbeat(
        product_name: str = Query(...),
        product_module: str = Query(...),
        product_feature: str = Query(...),
        product_tenant: str = Query(...),
    ) -> dict[str, Any]:
        """V2 heartbeat — confirms rate limiter middleware is active."""
        response: dict[str, Any] = {
            "message": "heartbeat v2",
            "product_name": product_name,
            "product_module": product_module,
            "product_feature": product_feature,
            "product_tenant": product_tenant,
        }

        if heartbeat_extra:
            response.update(heartbeat_extra)
        return response

    return router
