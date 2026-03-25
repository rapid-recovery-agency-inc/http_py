"""Request logger SQL helpers."""

# ruff: noqa: S608

import re

from psycopg_pool import PoolTimeout

from http_py.logging.services import create_logger
from http_py.database.exceptions import DatabaseTimeoutError
from http_py.request_logger.types import RequestArgs


logger = create_logger(__name__)

DEFAULT_REQUEST_TABLE = "request_logger_request"

_TABLE_PREFIX_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def resolve_table_name(default: str, table_prefix: str | None = None) -> str:
    """Build a table name with an optional prefix.

    Returns *default* unchanged when *table_prefix* is ``None``.
    Otherwise returns ``"{table_prefix}_{default}"``.

    Raises ``ValueError`` if the prefix contains characters that are
    not valid in a SQL identifier.
    """
    if table_prefix is None:
        return default
    if not _TABLE_PREFIX_RE.match(table_prefix):
        raise ValueError(
            f"Invalid table_prefix {table_prefix!r}: "
            "must contain only letters, digits, and underscores, "
            "and must not start with a digit"
        )
    return f"{table_prefix}_{default}"


def _build_request_insert_query(table: str) -> str:
    return f"""
        INSERT INTO
            {table}
            (
                path, product_name, product_module, product_feature,
                product_tenant, from_cache, request_headers,
                request_body, response_headers, response_body,
                status_code, duration_ms
            )
        VALUES
            (%(path)s,%(product_name)s,%(product_module)s,%(product_feature)s,
            %(product_tenant)s, %(from_cache)s, %(request_headers)s,
            %(request_body)s,%(response_headers)s, %(response_body)s,
            %(status_code)s, %(duration_ms)s)
    """


async def save_request(args: RequestArgs, table_prefix: str | None = None) -> None:
    if any(
        v is None
        for v in [
            args.path,
        ]
    ):
        raise ValueError("save_request: 'path' is  required")

    table = resolve_table_name(DEFAULT_REQUEST_TABLE, table_prefix)

    try:
        async with args.ctx.writer_pool.connection() as conn:
            async with conn.cursor() as cur:
                query = _build_request_insert_query(table)
                await cur.execute(
                    query,
                    {
                        "path": args.path,
                        "product_name": args.product_name,
                        "product_module": args.product_module,
                        "product_feature": args.product_feature,
                        "product_tenant": args.product_tenant,
                        "from_cache": args.from_cache,
                        "request_headers": args.request_headers,
                        "request_body": args.request_body,
                        "response_headers": args.response_headers,
                        "response_body": args.response_body,
                        "status_code": args.status_code,
                        "duration_ms": args.duration_ms,
                    },
                )
    except (PoolTimeout, DatabaseTimeoutError) as e:
        logger.exception("save_request: PoolTimeout occurred", exc_info=e)
        raise e
