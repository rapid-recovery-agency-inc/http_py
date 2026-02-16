from psycopg_pool import PoolTimeout

from http_py.logging.logging import create_logger
from http_py.request_logger.types import RequestArgs


logger = create_logger(__name__)


async def save_request(args: RequestArgs) -> None:
    if any(
        v is None
        for v in [
            args.path,
        ]
    ):
        raise ValueError("save_request: 'path' is  required")

    try:
        async with args.ctx.writer_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO request_logger_request
                    (path, product_name, product_module, product_feature,
                    product_tenant, from_cache, request_headers,
                    request_body, response_headers, response_body)
                    VALUES
                    (%(path)s,%(product_name)s,%(product_module)s,%(product_feature)s,
                    %(product_tenant)s, %(from_cache)s, %(request_headers)s,
                    %(request_body)s,%(response_headers)s, %(response_body)s)
                    """,
                    {
                        "path": args.path,
                        "product_name": args.ctx.product_name,
                        "product_module": args.ctx.product_module,
                        "product_feature": args.ctx.product_feature,
                        "product_tenant": args.ctx.product_tenant,
                        "from_cache": args.ctx.from_cache,
                        "request_headers": args.request_headers,
                        "request_body": args.request_body,
                        "response_headers": args.response_headers,
                        "response_body": args.response_body,
                    },
                )
    except PoolTimeout as e:
        logger.exception("save_request: PoolTimeout occurred", exc_info=e)
        raise e
