# http-py

A minimalistic library to share code between Python APIs and microservices that use HTTP.

## Features

- **HTTP Constants**: Status codes, headers, methods, and content types
- **Standardized Responses**: Consistent JSON response models for success, error, and paginated data
- **Custom Exceptions**: HTTP-specific exceptions with detailed error handling
- **Middleware Utilities**: CORS and logging middleware helpers
- **Utility Functions**: Common HTTP operations like token extraction and pagination
- **Type Safety**: Full type hints with Pydantic models and MyPy support
- **Well Tested**: Comprehensive test coverage

## Installation

```bash
pip install http-py
```

For development:

```bash
pip install -e ".[dev]"
```

## Quick Start

### Using HTTP Constants

```python
from http_py import HTTPStatus, HTTPMethod, HTTPHeader, ContentType

# Use status codes
status = HTTPStatus.OK  # 200
not_found = HTTPStatus.NOT_FOUND  # 404

# Use HTTP methods
method = HTTPMethod.GET  # "GET"

# Use headers
content_type = HTTPHeader.CONTENT_TYPE  # "Content-Type"

# Use content types
json_type = ContentType.JSON  # "application/json"
```

### Creating Standardized Responses

```python
from http_py import create_success_response, create_error_response

# Success response
response = create_success_response(
    data={"id": 1, "name": "John Doe"},
    message="User retrieved successfully"
)
# Returns:
# {
#     "success": True,
#     "data": {"id": 1, "name": "John Doe"},
#     "message": "User retrieved successfully"
# }

# Error response
error = create_error_response(
    error="User not found",
    status_code=404
)
# Returns:
# {
#     "success": False,
#     "error": "User not found",
#     "status_code": 404
# }
```

### Using HTTP Exceptions

```python
from http_py import (
    NotFoundException,
    BadRequestException,
    UnauthorizedException,
    http_exception_handler
)
from http_py.models import ErrorDetail

# Raise exceptions
raise NotFoundException(message="User not found")

# With detailed errors
details = [
    ErrorDetail(field="email", message="Invalid email format"),
    ErrorDetail(field="password", message="Password too short")
]
raise BadRequestException(message="Validation failed", details=details)

# Handle exceptions
try:
    # Your code here
    raise NotFoundException(message="Resource not found")
except HTTPException as e:
    error_dict = http_exception_handler(e)
    # Returns standardized error dictionary
```

### Paginated Responses

```python
from http_py import create_paginated_response, calculate_offset

# Calculate database offset
page = 2
page_size = 10
offset = calculate_offset(page, page_size)  # Returns 10

# Create paginated response
response = create_paginated_response(
    data=[{"id": 1}, {"id": 2}, {"id": 3}],
    page=1,
    page_size=10,
    total_items=100
)
# Returns:
# {
#     "success": True,
#     "data": [...],
#     "pagination": {
#         "page": 1,
#         "page_size": 10,
#         "total_items": 100,
#         "total_pages": 10
#     }
# }
```

### CORS Middleware

```python
from http_py import CORSMiddleware

# Create CORS middleware
cors = CORSMiddleware(
    allow_origins=["https://example.com", "https://app.example.com"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True,
    max_age=3600
)

# Get CORS headers
headers = cors.get_headers(origin="https://example.com")
# Returns:
# {
#     "Access-Control-Allow-Origin": "https://example.com",
#     "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
#     "Access-Control-Allow-Headers": "Content-Type, Authorization",
#     "Access-Control-Allow-Credentials": "true",
#     "Access-Control-Max-Age": "3600"
# }
```

### Logging Middleware

```python
from http_py import LoggingMiddleware

# Create logging middleware
logger = LoggingMiddleware(
    logger_name="my_api",
    log_request_body=True,
    log_response_body=True
)

# Log requests
logger.log_request(
    method="POST",
    path="/api/users",
    headers={"Content-Type": "application/json"}
)

# Log responses
logger.log_response(
    method="POST",
    path="/api/users",
    status_code=201,
    duration_ms=150.5
)
```

### Token Extraction

```python
from http_py import extract_bearer_token

# Extract bearer token from Authorization header
token = extract_bearer_token("Bearer abc123xyz")
# Returns: "abc123xyz"
```

## API Reference

### Constants

- **HTTPStatus**: Enum of HTTP status codes (200, 404, 500, etc.)
- **HTTPMethod**: Enum of HTTP methods (GET, POST, PUT, etc.)
- **HTTPHeader**: Common HTTP header names
- **ContentType**: Common content type values

### Models

- **SuccessResponse[T]**: Generic success response model
- **ErrorResponse**: Error response model
- **ErrorDetail**: Detailed error information
- **PaginatedResponse[T]**: Paginated response model
- **PaginationMetadata**: Pagination information

### Exceptions

- **HTTPException**: Base HTTP exception
- **BadRequestException**: 400 Bad Request
- **UnauthorizedException**: 401 Unauthorized
- **ForbiddenException**: 403 Forbidden
- **NotFoundException**: 404 Not Found
- **MethodNotAllowedException**: 405 Method Not Allowed
- **ConflictException**: 409 Conflict
- **UnprocessableEntityException**: 422 Unprocessable Entity
- **TooManyRequestsException**: 429 Too Many Requests
- **InternalServerErrorException**: 500 Internal Server Error
- **ServiceUnavailableException**: 503 Service Unavailable

### Utilities

- **create_success_response(data, message)**: Create success response
- **create_error_response(error, status_code, details)**: Create error response
- **create_paginated_response(data, page, page_size, total_items, message)**: Create paginated response
- **calculate_offset(page, page_size)**: Calculate database offset
- **extract_bearer_token(authorization)**: Extract token from Authorization header
- **http_exception_handler(exc)**: Convert HTTPException to dict

### Middleware

- **CORSMiddleware**: CORS configuration helper
- **LoggingMiddleware**: Request/response logging
- **timing_middleware**: Decorator for timing function execution

## Development

### Setup

```bash
# Install dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_models.py

# Run with verbose output
pytest -v
```

### Linting and Type Checking

```bash
# Run ruff linter
ruff check .

# Format code
ruff format .

# Run mypy type checker
mypy src/http_py
```

## Requirements

- Python 3.12+
- pydantic >= 2.0.0

## License

MIT