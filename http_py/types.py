"""Type definitions for the AWS module."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class AWSEnvironment(Protocol):
    """Protocol for any dataclass (or subclass) that carries AWS config keys."""

    AWS_REGION: str
    ENVIRONMENT_SECRET_NAME: str


@runtime_checkable
class PostgressEnvironment(Protocol):
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_WRITER_HOST: str
    DB_READER_HOSTS: str
    DB_PORT: str
    DB_NAME: str
    DB_POOL_TIMEOUT: int
    DB_MIN_POOL_SIZE: int
    DB_MAX_POOL_SIZE: int
    DB_POOL_MAX_IDLE_TIME_SECONDS: int
