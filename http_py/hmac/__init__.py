"""HMAC signature verification module for HTTP API authentication.

Provides request signature validation using HMAC-SHA256.
"""

from http_py.hmac.utils import sign
from http_py.hmac.services import require_hmac_signature, hmac_dependency_factory
from http_py.hmac.constants import (
    HMAC_INVALID_SIGNATURE,
    HMAC_MISSING_SIGNATURE,
    HMAC_UNSUPPORTED_METHOD,
)
from http_py.hmac.exceptions import HMACException


__all__ = [
    # Constants
    "HMAC_INVALID_SIGNATURE",
    "HMAC_MISSING_SIGNATURE",
    "HMAC_UNSUPPORTED_METHOD",
    # Exceptions
    "HMACException",
    # Functions
    "require_hmac_signature",
    "hmac_dependency_factory",
    "sign",
]
