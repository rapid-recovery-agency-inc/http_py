"""Tests for table_prefix support in request_logger and rate_limiter."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from psycopg import sql

from http_py.request_logger.types import RequestArgs, RequestLoggerOverride
from http_py.request_logger.utils import save_request, resolve_table_name
from http_py.rate_limiter.services import RateLimiterMiddleware
from http_py.request_logger.services import DatabaseRequestLoggerMiddleware


def test_no_prefix_returns_default() -> None:
    assert resolve_table_name("my_table") == "my_table"


def test_none_prefix_returns_default() -> None:
    assert resolve_table_name("my_table", None) == "my_table"


def test_prefix_prepends_with_underscore() -> None:
    assert (
        resolve_table_name("request_logger_request", "user_service")
        == "user_service_request_logger_request"
    )


def test_prefix_with_digits() -> None:
    assert resolve_table_name("my_table", "svc_v2") == "svc_v2_my_table"


def test_prefix_starting_with_digit_raises() -> None:
    with pytest.raises(ValueError):
        resolve_table_name("my_table", "2bad")


def test_prefix_with_special_chars_raises() -> None:
    with pytest.raises(ValueError):
        resolve_table_name("my_table", "drop;--")


def test_prefix_with_spaces_raises() -> None:
    with pytest.raises(ValueError):
        resolve_table_name("my_table", "bad prefix")


def test_prefix_with_dash_raises() -> None:
    with pytest.raises(ValueError):
        resolve_table_name("my_table", "bad-prefix")


def test_prefix_underscore_start_ok() -> None:
    assert resolve_table_name("tbl", "_private") == "_private_tbl"


def test_request_logger_middleware_stores_table_prefix() -> None:
    app = MagicMock()
    ctx_factory = MagicMock()
    middleware = DatabaseRequestLoggerMiddleware(
        app=app,
        path_whitelist=["/health"],
        create_service_context=ctx_factory,
        table_prefix="user_service",
    )
    assert middleware.table_prefix == "user_service"


def test_request_logger_middleware_table_prefix_defaults_to_none() -> None:
    app = MagicMock()
    ctx_factory = MagicMock()
    middleware = DatabaseRequestLoggerMiddleware(
        app=app,
        path_whitelist=["/health"],
        create_service_context=ctx_factory,
    )
    assert middleware.table_prefix is None


def test_request_logger_middleware_with_override_and_table_prefix() -> None:
    app = MagicMock()
    ctx_factory = MagicMock()
    override = RequestLoggerOverride(product_name="default-product")
    middleware = DatabaseRequestLoggerMiddleware(
        app=app,
        path_whitelist=["/health"],
        create_service_context=ctx_factory,
        override=override,
        table_prefix="billing",
    )
    assert middleware.table_prefix == "billing"
    assert middleware.override is override


def test_rate_limiter_middleware_stores_table_prefix() -> None:
    app = MagicMock()
    ctx_factory = MagicMock()
    middleware = RateLimiterMiddleware(
        app=app,
        path_whitelist=["/health"],
        create_service_context=ctx_factory,
        table_prefix="user_service",
    )
    assert middleware.table_prefix == "user_service"


def test_rate_limiter_middleware_table_prefix_defaults_to_none() -> None:
    app = MagicMock()
    ctx_factory = MagicMock()
    middleware = RateLimiterMiddleware(
        app=app,
        path_whitelist=["/health"],
        create_service_context=ctx_factory,
    )
    assert middleware.table_prefix is None


def _make_mock_ctx() -> MagicMock:
    ctx = MagicMock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.execute = AsyncMock()
    mock_cursor.__aenter__ = AsyncMock(return_value=mock_cursor)
    mock_cursor.__aexit__ = AsyncMock(return_value=False)
    mock_conn.cursor = MagicMock(return_value=mock_cursor)
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=False)
    ctx.writer_pool.connection = MagicMock(return_value=mock_conn)
    ctx.mock_cursor = mock_cursor
    return ctx


def _make_args(ctx: MagicMock) -> RequestArgs:
    return RequestArgs(
        ctx=ctx,
        path="/api/users",
        from_cache=False,
        product_name="product",
        product_module="module",
        product_feature="feature",
        product_tenant="tenant",
        request_headers="{}",
        request_body="{}",
        response_headers="{}",
        response_body="{}",
        status_code=200,
        duration_ms=42,
    )


def test_save_request_default_table() -> None:
    ctx = _make_mock_ctx()
    args = _make_args(ctx)

    asyncio.run(save_request(args))

    mock_cursor = ctx.mock_cursor
    mock_cursor.execute.assert_called_once()
    query = mock_cursor.execute.call_args[0][0]
    rendered = query.as_string(None)
    assert '"request_logger_request"' in rendered


def test_save_request_with_prefix() -> None:
    ctx = _make_mock_ctx()
    args = _make_args(ctx)

    asyncio.run(save_request(args, table_prefix="user_service"))

    mock_cursor = ctx.mock_cursor
    query = mock_cursor.execute.call_args[0][0]
    rendered = query.as_string(None)
    assert '"user_service_request_logger_request"' in rendered
    assert '"request_logger_request"' not in rendered.replace(
        '"user_service_request_logger_request"', ""
    )


def test_save_request_invalid_prefix_raises() -> None:
    ctx = _make_mock_ctx()
    args = _make_args(ctx)

    with pytest.raises(ValueError):
        asyncio.run(save_request(args, table_prefix="drop;--"))

    ctx.mock_cursor.execute.assert_not_called()


def test_save_request_uses_sql_identifier() -> None:
    ctx = _make_mock_ctx()
    args = _make_args(ctx)

    asyncio.run(save_request(args, table_prefix="svc"))

    query = ctx.mock_cursor.execute.call_args[0][0]
    assert isinstance(query, sql.Composed)
