from collections.abc import Callable, Awaitable

from starlette.requests import Request


HMACFactoryDependency = Callable[[Request], Awaitable[None]]
