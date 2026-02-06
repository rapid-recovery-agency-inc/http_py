"""Example usage of http-py library."""

from http_py import (
    BadRequestException,
    CORSMiddleware,
    HTTPStatus,
    LoggingMiddleware,
    NotFoundException,
    calculate_offset,
    create_error_response,
    create_paginated_response,
    create_success_response,
    extract_bearer_token,
    http_exception_handler,
)
from http_py.models import ErrorDetail


def example_success_response() -> None:
    """Example of creating a success response."""
    print("=== Success Response Example ===")
    response = create_success_response(
        data={"id": 1, "name": "John Doe", "email": "john@example.com"},
        message="User retrieved successfully",
    )
    print(response)
    print()


def example_error_response() -> None:
    """Example of creating an error response."""
    print("=== Error Response Example ===")
    details = [
        ErrorDetail(field="email", message="Invalid email format", code="INVALID_EMAIL"),
        ErrorDetail(field="password", message="Password too short", code="PASSWORD_TOO_SHORT"),
    ]
    response = create_error_response(
        error="Validation failed",
        status_code=HTTPStatus.BAD_REQUEST,
        details=details,
    )
    print(response)
    print()


def example_paginated_response() -> None:
    """Example of creating a paginated response."""
    print("=== Paginated Response Example ===")
    users = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
        {"id": 3, "name": "Charlie"},
    ]
    response = create_paginated_response(
        data=users, page=1, page_size=10, total_items=100, message="Users retrieved"
    )
    print(response)
    print()


def example_exceptions() -> None:
    """Example of using HTTP exceptions."""
    print("=== HTTP Exceptions Example ===")
    try:
        raise NotFoundException(message="User with ID 123 not found")
    except NotFoundException as e:
        error_dict = http_exception_handler(e)
        print(f"Exception handled: {error_dict}")

    try:
        details = [ErrorDetail(field="email", message="Email already exists")]
        raise BadRequestException(message="User creation failed", details=details)
    except BadRequestException as e:
        error_dict = http_exception_handler(e)
        print(f"Exception handled: {error_dict}")
    print()


def example_cors_middleware() -> None:
    """Example of using CORS middleware."""
    print("=== CORS Middleware Example ===")
    cors = CORSMiddleware(
        allow_origins=["https://example.com", "https://app.example.com"],
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_credentials=True,
    )
    headers = cors.get_headers(origin="https://example.com")
    print(f"CORS Headers: {headers}")
    print()


def example_logging_middleware() -> None:
    """Example of using logging middleware."""
    print("=== Logging Middleware Example ===")
    logger = LoggingMiddleware(logger_name="api_example")
    logger.log_request("POST", "/api/users", headers={"Content-Type": "application/json"})
    logger.log_response("POST", "/api/users", 201, 150.5)
    print("Logged request and response (check logs)")
    print()


def example_utility_functions() -> None:
    """Example of using utility functions."""
    print("=== Utility Functions Example ===")

    # Calculate database offset for pagination
    offset = calculate_offset(page=3, page_size=10)
    print(f"Offset for page 3: {offset}")

    # Extract bearer token
    token = extract_bearer_token("Bearer abc123xyz")
    print(f"Extracted token: {token}")

    invalid_token = extract_bearer_token("Basic abc123")
    print(f"Invalid auth header: {invalid_token}")
    print()


if __name__ == "__main__":
    example_success_response()
    example_error_response()
    example_paginated_response()
    example_exceptions()
    example_cors_middleware()
    example_logging_middleware()
    example_utility_functions()

    print("=== All examples completed successfully! ===")
