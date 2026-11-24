import asyncio
from dataclasses import dataclass

import pytest
from starlette.requests import Request

from http_py.hmac.services import (
    DEFAULT_HEADER_NAME,
    build_hmac_factory_dependency,
    require_hmac_signature,
    resolve_signature_header_name,
)
from http_py.hmac.utils import sign
from http_py.hmac.constants import HMAC_MISSING_SIGNATURE
from http_py.hmac.exceptions import HMACException


SECRET = "test-secret"


@dataclass(frozen=True)
class NewNameEnv:
    SECRETS: list[str]
    HMAC_SIGNATURE_HEADER_NAME: str


@dataclass(frozen=True)
class BothNamesEnv:
    SECRETS: list[str]
    HMAC_SIGNATURE_HEADER_NAME: str
    HMAC_HEADER_NAME: str


@dataclass(frozen=True)
class LegacyNameEnv:
    SECRETS: list[str]
    HMAC_HEADER_NAME: str


@dataclass(frozen=True)
class NoNameEnv:
    SECRETS: list[str]


def make_request(path: str, query_string: bytes, headers: list[tuple[bytes, bytes]]) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("127.0.0.1", 12345),
            "path": path,
            "query_string": query_string,
            "headers": headers,
        }
    )


def signed_request(header_name: str) -> Request:
    url = "http://testserver/protected?b=2&a=1"
    signature = sign(SECRET, url, {"b": "2", "a": "1"})
    return make_request(
        "/protected",
        b"b=2&a=1",
        [(header_name.lower().encode("utf-8"), signature.encode("utf-8"))],
    )


def test_resolve_prefers_new_name() -> None:
    env = BothNamesEnv(
        SECRETS=[SECRET],
        HMAC_SIGNATURE_HEADER_NAME="X-RRA-Signature",
        HMAC_HEADER_NAME="X-Legacy-Signature",
    )
    assert resolve_signature_header_name(env) == "X-RRA-Signature"


def test_resolve_falls_back_to_legacy_name() -> None:
    env = LegacyNameEnv(SECRETS=[SECRET], HMAC_HEADER_NAME="X-Legacy-Signature")
    with pytest.warns(DeprecationWarning, match="HMAC_HEADER_NAME is deprecated"):
        assert resolve_signature_header_name(env) == "X-Legacy-Signature"


def test_resolve_defaults_when_no_name_set() -> None:
    assert resolve_signature_header_name(NoNameEnv(SECRETS=[SECRET])) == DEFAULT_HEADER_NAME


def test_require_hmac_signature_accepts_new_header_name() -> None:
    env = NewNameEnv(SECRETS=[SECRET], HMAC_SIGNATURE_HEADER_NAME="X-RRA-Signature")
    asyncio.run(require_hmac_signature(signed_request("X-RRA-Signature"), env))


def test_require_hmac_signature_accepts_legacy_header_name() -> None:
    env = LegacyNameEnv(SECRETS=[SECRET], HMAC_HEADER_NAME="X-Legacy-Signature")
    with pytest.warns(DeprecationWarning):
        asyncio.run(
            require_hmac_signature(signed_request("X-Legacy-Signature"), env)
        )


def test_require_hmac_signature_accepts_default_header_name() -> None:
    env = NoNameEnv(SECRETS=[SECRET])
    asyncio.run(require_hmac_signature(signed_request(DEFAULT_HEADER_NAME), env))


def test_require_hmac_signature_rejects_missing_signature() -> None:
    env = NewNameEnv(SECRETS=[SECRET], HMAC_SIGNATURE_HEADER_NAME="X-RRA-Signature")
    request = make_request("/protected", b"", [])
    with pytest.raises(HMACException) as exc_info:
        asyncio.run(require_hmac_signature(request, env))
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == HMAC_MISSING_SIGNATURE


def test_require_hmac_signature_rejects_wrong_header_name() -> None:
    env = NewNameEnv(SECRETS=[SECRET], HMAC_SIGNATURE_HEADER_NAME="X-RRA-Signature")
    with pytest.raises(HMACException):
        asyncio.run(
            require_hmac_signature(signed_request("X-Other-Signature"), env)
        )


def test_factory_dependency_accepts_env_with_only_legacy_name() -> None:
    env = LegacyNameEnv(SECRETS=[SECRET], HMAC_HEADER_NAME="X-Legacy-Signature")
    dependency = build_hmac_factory_dependency(env)
    with pytest.warns(DeprecationWarning):
        asyncio.run(dependency(signed_request("X-Legacy-Signature")))


def test_factory_dependency_accepts_env_with_no_header_name() -> None:
    dependency = build_hmac_factory_dependency(NoNameEnv(SECRETS=[SECRET]))
    asyncio.run(dependency(signed_request(DEFAULT_HEADER_NAME)))


def test_factory_dependency_rejects_empty_secrets() -> None:
    with pytest.raises(ValueError, match="SECRETS must be a non-empty list"):
        build_hmac_factory_dependency(NoNameEnv(SECRETS=[]))
