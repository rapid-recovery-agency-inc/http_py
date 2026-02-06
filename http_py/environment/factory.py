"""Entry point for the environment library.

Call :func:`create_environment` once at application startup with your
frozen ``@dataclass`` type.  Then re-export the bound ``env`` and
``set_environment`` methods throughout your application::

    import os
    from dataclasses import dataclass, field
    from http_py.environment import create_environment

    @dataclass(frozen=True)
    class AppEnv:
        DEBUG: bool = False
        DB_HOST: str = "localhost"
        DB_PORT: int = 5432

    _manager = create_environment(AppEnv)
    env = _manager.env
    set_environment = _manager.set_environment

    # Seed from os.environ explicitly:
    set_environment(os.environ)
"""

from typing import TypeVar

from http_py.environment.manager import EnvironmentManager


T = TypeVar("T")


def create_environment(
    dataclass_type: type[T],
    *,
    mandatory_keys: list[str] | None = None,
) -> EnvironmentManager[T]:
    """Create an :class:`EnvironmentManager` bound to *dataclass_type*.

    This is intended to be called **once** during application bootstrap.
    The returned manager's :meth:`~EnvironmentManager.env` and
    :meth:`~EnvironmentManager.set_environment` methods can be
    destructured and re-exported as plain module-level symbols::

        _mgr = create_environment(MyEnv)
        env = _mgr.env
        set_environment = _mgr.set_environment

    .. note::

        The library does **not** load ``os.environ`` automatically.
        Call ``set_environment(os.environ)`` explicitly to seed from
        the host environment.

    Custom converters for individual fields are declared via
    ``field(metadata={"converter": my_fn})`` on the dataclass itself.

    Args:
        dataclass_type: A **frozen** ``@dataclass`` class defining the
            shape and types of the environment.
        mandatory_keys: Field names that :meth:`EnvironmentManager.load`
            will require before accepting external data.

    Returns:
        A fully initialised :class:`EnvironmentManager` instance.
    """
    return EnvironmentManager(
        dataclass_type,
        mandatory_keys=mandatory_keys,
    )
