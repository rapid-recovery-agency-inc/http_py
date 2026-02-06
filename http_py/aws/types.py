"""Type definitions for the AWS module."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class AWSEnvironment(Protocol):
    """Protocol for any dataclass (or subclass) that carries AWS config keys."""

    AWS_REGION: str
    ENVIRONMENT_SECRET_NAME: str