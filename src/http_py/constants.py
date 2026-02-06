"""HTTP constants including status codes, headers, methods, and content types."""

from enum import IntEnum, StrEnum


class HTTPStatus(IntEnum):
    """HTTP status codes."""

    # 2xx Success
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204

    # 3xx Redirection
    MOVED_PERMANENTLY = 301
    FOUND = 302
    NOT_MODIFIED = 304
    TEMPORARY_REDIRECT = 307
    PERMANENT_REDIRECT = 308

    # 4xx Client Errors
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    NOT_ACCEPTABLE = 406
    CONFLICT = 409
    GONE = 410
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429

    # 5xx Server Errors
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504


class HTTPMethod(StrEnum):
    """HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class HTTPHeader(StrEnum):
    """Common HTTP headers."""

    CONTENT_TYPE = "Content-Type"
    CONTENT_LENGTH = "Content-Length"
    AUTHORIZATION = "Authorization"
    ACCEPT = "Accept"
    USER_AGENT = "User-Agent"
    REFERER = "Referer"
    ORIGIN = "Origin"
    HOST = "Host"
    X_FORWARDED_FOR = "X-Forwarded-For"
    X_REQUEST_ID = "X-Request-ID"
    X_CORRELATION_ID = "X-Correlation-ID"
    CACHE_CONTROL = "Cache-Control"
    ETAG = "ETag"
    LOCATION = "Location"
    ACCESS_CONTROL_ALLOW_ORIGIN = "Access-Control-Allow-Origin"
    ACCESS_CONTROL_ALLOW_METHODS = "Access-Control-Allow-Methods"
    ACCESS_CONTROL_ALLOW_HEADERS = "Access-Control-Allow-Headers"
    ACCESS_CONTROL_ALLOW_CREDENTIALS = "Access-Control-Allow-Credentials"
    ACCESS_CONTROL_MAX_AGE = "Access-Control-Max-Age"


class ContentType(StrEnum):
    """Common content types."""

    JSON = "application/json"
    XML = "application/xml"
    HTML = "text/html"
    PLAIN = "text/plain"
    FORM = "application/x-www-form-urlencoded"
    MULTIPART = "multipart/form-data"
    OCTET_STREAM = "application/octet-stream"
    PDF = "application/pdf"
    CSV = "text/csv"
