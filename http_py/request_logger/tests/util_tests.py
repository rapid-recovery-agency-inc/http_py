"""Tests for table_prefix support in request_logger and rate_limiter."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from psycopg import sql

from http_py.request_logger.types import RequestArgs, RequestLoggerOverride
from http_py.request_logger.utils import (
    save_request,
    resolve_table_name,
)
from http_py.rate_limiter.services import RateLimiterMiddleware
from http_py.request_logger.services import DatabaseRequestLoggerMiddleware


# ── resolve_table_name ──────────────────────────────────────────────


class TestResolveTableName(unittest.TestCase):
    """Tests for the resolve_table_name helper."""

    def test_no_prefix_returns_default(self) -> None:
        self.assertEqual(resolve_table_name("my_table"), "my_table")

    def test_none_prefix_returns_default(self) -> None:
        self.assertEqual(resolve_table_name("my_table", None), "my_table")

    def test_prefix_prepends_with_underscore(self) -> None:
        self.assertEqual(
            resolve_table_name("request_logger_request", "user_service"),
            "user_service_request_logger_request",
        )

    def test_prefix_with_digits(self) -> None:
        self.assertEqual(
            resolve_table_name("my_table", "svc_v2"),
            "svc_v2_my_table",
        )

    def test_prefix_starting_with_digit_raises(self) -> None:
        with self.assertRaises(ValueError):
            resolve_table_name("my_table", "2bad")

    def test_prefix_with_special_chars_raises(self) -> None:
        with self.assertRaises(ValueError):
            resolve_table_name("my_table", "drop;--")

    def test_prefix_with_spaces_raises(self) -> None:
        with self.assertRaises(ValueError):
            resolve_table_name("my_table", "bad prefix")

    def test_prefix_with_dash_raises(self) -> None:
        with self.assertRaises(ValueError):
            resolve_table_name("my_table", "bad-prefix")

    def test_prefix_underscore_start_ok(self) -> None:
        self.assertEqual(
            resolve_table_name("tbl", "_private"),
            "_private_tbl",
        )


# ── DatabaseRequestLoggerMiddleware ─────────────────────────────────


class TestDatabaseRequestLoggerMiddlewareTablePrefix(unittest.TestCase):
    """Tests for table_prefix on DatabaseRequestLoggerMiddleware."""

    def test_middleware_stores_table_prefix(self) -> None:
        app = MagicMock()
        ctx_factory = MagicMock()
        middleware = DatabaseRequestLoggerMiddleware(
            app=app,
            path_whitelist=["/health"],
            create_service_context=ctx_factory,
            table_prefix="user_service",
        )
        self.assertEqual(middleware.table_prefix, "user_service")

    def test_middleware_table_prefix_defaults_to_none(self) -> None:
        app = MagicMock()
        ctx_factory = MagicMock()
        middleware = DatabaseRequestLoggerMiddleware(
            app=app,
            path_whitelist=["/health"],
            create_service_context=ctx_factory,
        )
        self.assertIsNone(middleware.table_prefix)

    def test_middleware_with_override_and_table_prefix(self) -> None:
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
        self.assertEqual(middleware.table_prefix, "billing")
        self.assertEqual(middleware.override, override)


# ── RateLimiterMiddleware ───────────────────────────────────────────


class TestRateLimiterMiddlewareTablePrefix(unittest.TestCase):
    """Tests for table_prefix on RateLimiterMiddleware."""

    def test_middleware_stores_table_prefix(self) -> None:
        app = MagicMock()
        ctx_factory = MagicMock()
        middleware = RateLimiterMiddleware(
            app=app,
            path_whitelist=["/health"],
            create_service_context=ctx_factory,
            table_prefix="user_service",
        )
        self.assertEqual(middleware.table_prefix, "user_service")

    def test_middleware_table_prefix_defaults_to_none(self) -> None:
        app = MagicMock()
        ctx_factory = MagicMock()
        middleware = RateLimiterMiddleware(
            app=app,
            path_whitelist=["/health"],
            create_service_context=ctx_factory,
        )
        self.assertIsNone(middleware.table_prefix)


# ── save_request with table_prefix ──────────────────────────────────


class TestSaveRequestTablePrefix(unittest.TestCase):
    """Tests for table_prefix in save_request SQL."""

    def _make_mock_ctx(self) -> MagicMock:
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
        ctx._mock_cursor = mock_cursor
        return ctx

    def _make_args(self, ctx: MagicMock) -> RequestArgs:
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

    def test_save_request_default_table(self) -> None:
        """Without prefix, uses the default table name."""
        ctx = self._make_mock_ctx()
        args = self._make_args(ctx)

        asyncio.run(save_request(args))

        mock_cursor = ctx._mock_cursor
        mock_cursor.execute.assert_called_once()
        query = mock_cursor.execute.call_args[0][0]
        rendered = query.as_string(None)
        self.assertIn('"request_logger_request"', rendered)

    def test_save_request_with_prefix(self) -> None:
        """With prefix, table name is prefixed."""
        ctx = self._make_mock_ctx()
        args = self._make_args(ctx)

        asyncio.run(save_request(args, table_prefix="user_service"))

        mock_cursor = ctx._mock_cursor
        query = mock_cursor.execute.call_args[0][0]
        rendered = query.as_string(None)
        self.assertIn('"user_service_request_logger_request"', rendered)
        self.assertNotIn(
            '"request_logger_request"',
            rendered.replace('"user_service_request_logger_request"', ""),
        )

    def test_save_request_invalid_prefix_raises(self) -> None:
        """Invalid prefix is rejected before any DB call."""
        ctx = self._make_mock_ctx()
        args = self._make_args(ctx)

        with self.assertRaises(ValueError):
            asyncio.run(save_request(args, table_prefix="drop;--"))

        ctx._mock_cursor.execute.assert_not_called()

    def test_save_request_uses_sql_identifier(self) -> None:
        """The query object uses psycopg.sql.Identifier for safety."""
        ctx = self._make_mock_ctx()
        args = self._make_args(ctx)

        asyncio.run(save_request(args, table_prefix="svc"))

        query = ctx._mock_cursor.execute.call_args[0][0]
        self.assertIsInstance(query, sql.Composed)


if __name__ == "__main__":
    unittest.main()
