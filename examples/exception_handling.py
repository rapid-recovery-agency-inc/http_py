"""Examples: http_py.environment library usage.

Run with:  python environment.py
"""

from typing import Final
from fastapi.exceptions import FastAPI, RequestValidationError
from my_project import errors
from http_py.exception_handling.types import HandlerRule
from http_py.exception_handling.services import create_exception_handler
from http_py.exception_handling.utils import (build_validation_content,
                                              build_unexpected_content,
                                              build_client_error_content)

HANDLER_MAP: Final[dict[str, HandlerRule]] = {
    # 422 - Validation
    "validation": HandlerRule(
        RequestValidationError, 422, content_builder=build_validation_content
    ),
    # 404 - Not Found
    "task_not_found": HandlerRule(errors.TaskDoesNotExistException, 404),
    # 400 - Bad Request
    "data_source_error": HandlerRule(
        errors.DataSourceFetchException, 400, include_detail=False
    ),
    # 200 - Expected business conditions (prevent SQS retry)
    "no_locations": HandlerRule(errors.NoLocationsFoundException, 200, "debug",
                                False),
    # 423 - Locked
    "lock_failure": HandlerRule(errors.FailedLockAcquisitionException, 423,
                                "warning"),
    # 500 - Infrastructure / AWS
    "client_error": HandlerRule(
        errors.ClientError, 500, content_builder=build_client_error_content
    ),
    "scoring_engine_base": HandlerRule(errors.ScoringEngineBaseException, 500),
    # 500 - True catch-all (must be last)
    "unexpected": HandlerRule(
        Exception, 500, "critical", content_builder=build_unexpected_content
    ),
}

if __name__ == "__main__":
    app = FastAPI()
    exception_handler = create_exception_handler(
        handler_map=HANDLER_MAP,
    )
    app.add_exception_handler(RequestValidationError, exception_handler)
    app.add_exception_handler(Exception, exception_handler)
