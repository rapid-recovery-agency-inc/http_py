"""Examples: http_py.routers.create_v2_router usage.

This example demonstrates how any service (Foundd, Insightt, etc.)
uses create_v2_router to add rate-limited v2 endpoints.

The pattern:
1. http_py provides the router factory + rate limiter wiring
2. Each service provides its own handler with domain logic
3. Both coexist during transition — old routes untouched

Run with:  poetry run python examples/v2_router_example.py
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware

from http_py.routers import create_v2_router, RateLimiterParams
from http_py.rate_limiter import create_rate_limiter_middleware
from http_py.logging import create_logger


logger = create_logger(__name__)


async def my_service_handler(
  request: Request,
  params: RateLimiterParams
) -> JSONResponse:
  """Service-specific logic for the v2 endpoint.

    Args:
        request: The incoming Starlette request
        params:  Rate limiter params already extracted and validated
        (product_name, product_module, product_feature, product_tenant)

    Returns:
        JSONResponse with the service result
    """ 
  logger.info(
    f"v2 request: tenant={params.product_tenant}, "
    f"feature={params.product_feature}"
  )

  result = {"status": "ok", "tenant": params.product_tenant}
  return JSONResponse(content=result)


v2_router = create_v2_router(
  handler=my_service_handler,
  tags=["v2"],
  heartbeat_extra={"service": "my-service", "version": "2"},
)


async def create_service_context(request: Request):
    """Provide DB pools to the rate limiter. Replace with your env."""
    # from http_py.postgres import get_async_writer_connection_pool, ...
    # from http_py.context import ServiceContext
    # return ServiceContext(writer_pool=..., reader_pool=...)
    pass  # placeholder


RATE_LIMIT_WHITELIST = ["/", "/docs", "/openapi.json", "/heartbeat", "/favicon.ico"]

rate_limiter = create_rate_limiter_middleware(
  path_whitelist=RATE_LIMIT_WHITELIST,
  create_service_context=create_service_context,
)

@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # startup: initialize DB pools, environment, etc.
    yield
    # shutdown: cleanup pools


app = FastAPI(lifespan=lifespan)

app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limiter)

# Old routes stay untouched
# app.include_router(existing_router)

# New v2 routes — handler is service-specific, wiring is from http_py
app.include_router(v2_router, prefix="/v2")


# ──────────────────────────────────────────────────────────────────────
# 4. Transition plan
# ──────────────────────────────────────────────────────────────────────

# Step 1: Deploy with both old and /v2 routes active
# Step 2: Test /v2/ endpoints with rate limiter params
# Step 3: Validate rate limiter counts in rate_limiter_request table
# Step 4: Once validated, promote /v2 to / and remove old routes


# ──────────────────────────────────────────────────────────────────────
# 5. How to call the v2 endpoint
# ──────────────────────────────────────────────────────────────────────

# POST /v2/?product_name=foundd&product_module=scoring
#           &product_feature=calculate_hotspots&product_tenant=client-123
#
# POST /v2/heartbeat?product_name=foundd&product_module=scoring
#                    &product_feature=heartbeat&product_tenant=client-123


if __name__ == "__main__":
    uvicorn.run("v2_router_example:app", host="127.0.0.1", port=8000, reload=True)


  

