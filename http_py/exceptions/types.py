from typing import Any, Literal, Protocol, NamedTuple, runtime_checkable
from collections.abc import Callable, Sequence, Awaitable

from starlette.requests import Request


# Callback signature for rules that need custom response content.
# Returns (response_content, extra_log_fields).
ContentBuilderFn = Callable[
    [Request, Exception, dict[str, str]],
    Awaitable[tuple[dict[str, Any] | None, dict[str, Any]]],
]


class HandlerRule(NamedTuple):
    """Declarative rule mapping an exception type to a response shape.

    Args:
        exc_type: Exception class to match via isinstance.
        status_code: HTTP status code for the response.
        log_level: Logger method name ("debug", "error", etc.); None to suppress.
        include_detail: When True (and no content_builder), include str(exc)
            in response.
        content_builder: Async callback for custom response content and log extras.
    """

    exc_type: type[Exception]
    status_code: int
    log_level: Literal["debug", "info", "warning", "error", "critical"] | None = "error"
    include_detail: bool = True
    content_builder: ContentBuilderFn | None = None


@runtime_checkable
class FastAPIRequestValidationError(Protocol):
    def errors(self) -> Sequence[Any]: ...
