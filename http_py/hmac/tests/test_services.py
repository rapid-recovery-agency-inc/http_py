import asyncio
from dataclasses import dataclass

import pytest
from starlette.requests import Request

from http_py.hmac.utils import sign
from http_py.hmac.services import (
    DEFAULT_HEADER_NAME,
    require_hmac_signature,
    build_hmac_factory_dependency,
)
from http_py.hmac.constants import HMAC_MISSING_SIGNATURE
from http_py.hmac.exceptions import HMACException


SIGNING_KEY = "test-signing-key"


@dataclass(frozen=True)
class NamedEnv:
    SECRETS: list[str]
    HMAC_SIGNATURE_HEADER_NAME: str


@dataclass(frozen=True)
class NoNameEnv:
    SECRETS: list[str]


def signed_request(header_name: str) -> Request:
    url = "http://testserver/protected?b=2&a=1"
    signature = sign(SIGNING_KEY, url, {"b": "2", "a": "1"})
    return Request(
        {
            "type": "http",
            "method": "GET",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("127.0.0.1", 12345),
            "path": "/protected",
            "query_string": b"b=2&a=1",
            "headers": [
                (header_name.lower().encode("utf-8"), signature.encode("utf-8"))
            ],
        }
    )


def test_require_hmac_signature_uses_env_header_name() -> None:
    env = NamedEnv(
        SECRETS=[SIGNING_KEY], HMAC_SIGNATURE_HEADER_NAME="X-Custom-Signature"
    )
    asyncio.run(require_hmac_signature(signed_request("X-Custom-Signature"), env))


def test_require_hmac_signature_defaults_header_name() -> None:
    asyncio.run(
        require_hmac_signature(
            signed_request(DEFAULT_HEADER_NAME), NoNameEnv(SECRETS=[SIGNING_KEY])
        )
    )


def test_require_hmac_signature_rejects_missing_signature() -> None:
    env = NamedEnv(SECRETS=[SIGNING_KEY], HMAC_SIGNATURE_HEADER_NAME="X-RRA-Signature")
    request = signed_request("X-Other-Signature")
    with pytest.raises(HMACException) as exc_info:
        asyncio.run(require_hmac_signature(request, env))
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == HMAC_MISSING_SIGNATURE


def test_factory_dependency_works_without_header_name() -> None:
    dependency = build_hmac_factory_dependency(NoNameEnv(SECRETS=[SIGNING_KEY]))
    asyncio.run(dependency(signed_request(DEFAULT_HEADER_NAME)))


def test_factory_dependency_rejects_empty_SECRETS() -> None:
    with pytest.raises(ValueError, match="SECRETS must be a non-empty list"):
        build_hmac_factory_dependency(NoNameEnv(SECRETS=[]))
