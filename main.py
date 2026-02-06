from typing import Any
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import uvicorn
from fastapi import status, FastAPI
from psycopg_pool import PoolTimeout
from fastapi.encoders import jsonable_encoder
from starlette.status import HTTP_418_IM_A_TEAPOT
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers.background import (
    BackgroundScheduler,  # runs tasks in the background
)

from shared.errors import handle_validation_errors
from shared.fastapi import app_meta
from modules.logging.logging import create_logger
from shared.postgres import cleanup_connections_pools, warm_up_connections_pools
from shared.environment import env, load_aws_env
from modules.parsing.router import router as parsing_router
from modules.geocoding.tasks import clean_google_data
from modules.buildings.router import router as buildings_router
from modules.geocoding.router import router as geocoding_router
from modules.directions.router import router as directions_router
from modules.static_map.router import router as static_map_router
from modules.validation.router import router as validation_router
from shared.rate_limiter.middleware import create_rate_limiter_middleware


# Initialize logger
logger = create_logger(__name__)

scheduler = BackgroundScheduler()
trigger = IntervalTrigger(hours=24)  # Every 24 hours after a deployment
scheduler.add_job(clean_google_data, trigger)
scheduler.start()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: UP043
    load_aws_env()
    await warm_up_connections_pools()
    clean_google_data()
    try:
        yield
    finally:
        await cleanup_connections_pools()
        scheduler.shutdown()


# Initialize the FastAPI app
app = FastAPI(**app_meta, lifespan=lifespan)
app.middleware("http")(create_rate_limiter_middleware(path_whitelist=["/"]))


# Override the default validation error handler
@app.exception_handler(RequestValidationError)  # type: ignore
async def validation_exception_handler(
    _: Any, exc: RequestValidationError
) -> JSONResponse:
    errors = handle_validation_errors(exc)
    logger.error("Validation Error: errors=%r", errors)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"errors": errors, "body": exc.body}),
    )


@app.exception_handler(PoolTimeout)  # type: ignore
async def pool_timeout_exception_handler(
    request: Any, exception: PoolTimeout
) -> JSONResponse:
    logger.error(
        "handle_pool_timeout: request=%r, exception=%r", request.url.path, exception
    )
    return JSONResponse(
        status_code=HTTP_418_IM_A_TEAPOT,
        content={
            "message": "Oops! There seems to be a problem with the database. "
            "Give me some space, and try again later.",
        },
    )


@app.get("/")  # type: ignore
async def home() -> dict[str, str]:
    return {"docs_at": "/docs"}


app.include_router(buildings_router)
app.include_router(parsing_router)
app.include_router(geocoding_router)
app.include_router(directions_router)
app.include_router(static_map_router)
app.include_router(validation_router)

if __name__ == "__main__":
    if env().HTTP_LOGGING:
        uvicorn.run(app, host="127.0.0.1", port=8000)
    else:
        uvicorn.run(app, host="127.0.0.1", port=8000, log_config=None)
