"""Reusable environment management library.

The primary entry point is :func:`create_environment`.  See
:mod:`modules.environment.factory` for full usage documentation.
"""

from modules.environment.factory import create_environment
from modules.environment.manager import EnvironmentManager

__all__ = [
    "create_environment",
    "EnvironmentManager",
]
