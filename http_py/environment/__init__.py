"""Reusable environment management library.

The primary entry point is :func:`create_environment`.  See
:mod:`http_py.environment.factory` for full usage documentation.
"""

from http_py.environment.factory import create_environment
from http_py.environment.manager import EnvironmentManager

__all__ = [
    "create_environment",
    "EnvironmentManager",
]
