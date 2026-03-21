"""Tests for service_name support in the request logger."""

import asyncio
import unittest
from dataclasses import asdict
from unittest.mock import AsyncMock, MagicMock

from http_py.request_logger.types import RequestArgs, RequestLoggerOverride
from http_py.request_logger.utils import save_request
from http_py.request_logger.services import DatabaseRequestLoggerMiddleware


class TestRequestArgsServiceName(unittest.TestCase):
    """Tests for the service_name field on RequestArgs."""

    def _make_ctx(self) -> MagicMock:
        ctx = MagicMock()
        ctx.writer_pool = MagicMock()
        ctx.reader_pools = [MagicMock()]
        return ctx

    def test_request_args_default_service_name_is_none(self) -> None:
        ctx = self._make_ctx()
        args = RequestArgs(
            ctx=ctx,
            path="/api/test",
            from_cache=False,
            product_name="product",
            product_module="module",
            product_feature="feature",
            product_tenant="tenant",
            request_headers="{}",
            request_body="{}",
            response_headers="{}",
            response_body="{}",
        )
        self.assertIsNone(args.service_name)

    def test_request_args_with_service_name(self) -> None:
        ctx = self._make_ctx()
        args = RequestArgs(
            ctx=ctx,
            path="/api/test",
            from_cache=False,
            product_name="product",
            product_module="module",
            product_feature="feature",
            product_tenant="tenant",
            request_headers="{}",
            request_body="{}",
            response_headers="{}",
            response_body="{}",
            service_name="user-service",
        )
        self.assertEqual(args.service_name, "user-service")

    def test_request_args_service_name_in_asdict(self) -> None:
        ctx = self._make_ctx()
        args = RequestArgs(
            ctx=ctx,
            path="/api/test",
            from_cache=False,
            product_name="product",
            product_module="module",
            product_feature="feature",
            product_tenant="tenant",
            request_headers="{}",
            request_body="{}",
            response_headers="{}",
            response_body="{}",
            service_name="order-service",
        )
        d = asdict(args)
        self.assertEqual(d["service_name"], "order-service")

    def test_request_args_frozen_immutability(self) -> None:
        ctx = self._make_ctx()
        args = RequestArgs(
            ctx=ctx,
            path="/api/test",
            from_cache=False,
            product_name="product",
            product_module="module",
            product_feature="feature",
            product_tenant="tenant",
            request_headers="{}",
            request_body="{}",
            response_headers="{}",
            response_body="{}",
            service_name="my-service",
        )
        with self.assertRaises(AttributeError):
            args.service_name = "other-service"  # type: ignore[misc]


class TestRequestLoggerOverrideUnchanged(unittest.TestCase):
    """Verify RequestLoggerOverride does not include service_name."""

    def test_override_does_not_have_service_name(self) -> None:
        self.assertNotIn("service_name", RequestLoggerOverride._fields)

    def test_override_fields_unchanged(self) -> None:
        expected_fields = (
            "product_name",
            "product_module",
            "product_feature",
            "product_tenant",
            "request_headers",
            "request_body",
        )
        self.assertEqual(RequestLoggerOverride._fields, expected_fields)


class TestDatabaseRequestLoggerMiddlewareServiceName(unittest.TestCase):
    """Tests for service_name on DatabaseRequestLoggerMiddleware."""

    def test_middleware_stores_service_name(self) -> None:
        app = MagicMock()
        ctx_factory = MagicMock()
        middleware = DatabaseRequestLoggerMiddleware(
            app=app,
            path_whitelist=["/health"],
            create_service_context=ctx_factory,
            service_name="payment-service",
        )
        self.assertEqual(middleware.service_name, "payment-service")

    def test_middleware_service_name_defaults_to_none(self) -> None:
        app = MagicMock()
        ctx_factory = MagicMock()
        middleware = DatabaseRequestLoggerMiddleware(
            app=app,
            path_whitelist=["/health"],
            create_service_context=ctx_factory,
        )
        self.assertIsNone(middleware.service_name)

    def test_middleware_with_override_and_service_name(self) -> None:
        app = MagicMock()
        ctx_factory = MagicMock()
        override = RequestLoggerOverride(product_name="default-product")
        middleware = DatabaseRequestLoggerMiddleware(
            app=app,
            path_whitelist=["/health"],
            create_service_context=ctx_factory,
            override=override,
            service_name="billing-service",
        )
        self.assertEqual(middleware.service_name, "billing-service")
        self.assertEqual(middleware.override, override)


class TestSaveRequestServiceName(unittest.TestCase):
    """Tests for service_name in save_request SQL."""

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

    def test_save_request_includes_service_name_in_params(self) -> None:
        """Verify save_request passes service_name to the INSERT."""
        ctx = self._make_mock_ctx()
        args = RequestArgs(
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
            service_name="user-service",
            status_code=200,
            duration_ms=42,
        )

        asyncio.run(save_request(args))

        mock_cursor = ctx._mock_cursor
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args

        sql = call_args[0][0]
        self.assertIn("service_name", sql)

        params = call_args[0][1]
        self.assertEqual(params["service_name"], "user-service")

    def test_save_request_service_name_none(self) -> None:
        """Verify save_request handles None service_name."""
        ctx = self._make_mock_ctx()
        args = RequestArgs(
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

        asyncio.run(save_request(args))

        mock_cursor = ctx._mock_cursor
        call_args = mock_cursor.execute.call_args
        params = call_args[0][1]
        self.assertIsNone(params["service_name"])


if __name__ == "__main__":
    unittest.main()
