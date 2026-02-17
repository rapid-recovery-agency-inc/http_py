"""http_py - Utilities for building microservices and HTTP APIs.

This library provides common patterns and utilities for building
microservices and APIs with FastAPI and other Python frameworks.
"""

# Core utilities
from http_py.context import build_context
from http_py.logging import CustomLogger
from http_py.request import get_raw_body
from http_py.shortcuts import ok, created, not_found, no_content, bad_request

# Submodule re-exports for convenience
from http_py.environment import EnvironmentFactory
from http_py.exception_handling import ExceptionDeclaration, ExceptionHandlerFactory


__all__ = [
    # Context
    "build_context",
    # Request helpers
    "get_raw_body",
    # Response shortcuts
    "ok",
    "created",
    "no_content",
    "bad_request",
    "not_found",
    # Environment
    "EnvironmentFactory",
    # Logging
    "CustomLogger",
    # Exception handling
    "ExceptionHandlerFactory",
    "ExceptionDeclaration",
]

__version__ = "0.1.0"
