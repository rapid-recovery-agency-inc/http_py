"""Tests for constants module."""

from http_py.constants import ContentType, HTTPHeader, HTTPMethod, HTTPStatus


def test_http_status_values() -> None:
    """Test HTTP status code values."""
    assert HTTPStatus.OK == 200
    assert HTTPStatus.CREATED == 201
    assert HTTPStatus.BAD_REQUEST == 400
    assert HTTPStatus.UNAUTHORIZED == 401
    assert HTTPStatus.NOT_FOUND == 404
    assert HTTPStatus.INTERNAL_SERVER_ERROR == 500


def test_http_method_values() -> None:
    """Test HTTP method values."""
    assert HTTPMethod.GET == "GET"
    assert HTTPMethod.POST == "POST"
    assert HTTPMethod.PUT == "PUT"
    assert HTTPMethod.PATCH == "PATCH"
    assert HTTPMethod.DELETE == "DELETE"


def test_http_header_values() -> None:
    """Test HTTP header values."""
    assert HTTPHeader.CONTENT_TYPE == "Content-Type"
    assert HTTPHeader.AUTHORIZATION == "Authorization"
    assert HTTPHeader.ACCEPT == "Accept"
    assert HTTPHeader.X_REQUEST_ID == "X-Request-ID"


def test_content_type_values() -> None:
    """Test content type values."""
    assert ContentType.JSON == "application/json"
    assert ContentType.XML == "application/xml"
    assert ContentType.HTML == "text/html"
    assert ContentType.PLAIN == "text/plain"
