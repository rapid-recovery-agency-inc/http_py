"""Router factories for building versioned FastAPI routers.

Provides generic router factories that enforce rate limiter parameters
across all endpoints. Each service provides its own handler logic.

Example usage:
    from http_py.routers import create_v2_router, RateLimiterParams
"""

from .v2 import V2Handler, create_v2_router


__all__ = ["create_v2_router", "V2Handler"]
