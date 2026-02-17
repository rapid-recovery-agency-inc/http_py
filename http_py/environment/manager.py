"""Generic environment manager bound to a frozen dataclass shape."""

from typing import Any, TypeVar
from collections.abc import Mapping

from http_py.environment.coercion import to_dataclass_dict
from http_py.environment.validation import validate_keys


T = TypeVar("T")


class EnvironmentManager[T]:
    """Manages environment state for a frozen dataclass type ``T``.

    State is accumulated via successive :meth:`set_environment` calls.
    Each call merges the new coerced values **on top** of the previously
    stored state, so later calls override earlier values for the same
    keys.

    The library does **not** read ``os.environ`` automatically — the
    consuming application must seed it explicitly::

        set_environment(os.environ)

    Every call to :meth:`env` returns a **new** frozen ``T`` instance
    built from the accumulated state, so consumers never hold a stale
    reference.

    Args:
        dataclass_type: A frozen ``@dataclass`` class.
        mandatory_keys: Keys that :meth:`load` will enforce before
            accepting external data.
    """

    def __init__(
        self,
        dataclass_type: type[T],
        *,
        mandatory_keys: list[str] | None = None,
    ) -> None:
        self._dataclass_type = dataclass_type
        self._mandatory_keys = mandatory_keys or []
        self._state: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def env(self) -> T:
        """Return a **new** frozen ``T`` instance from the accumulated state."""
        return self._dataclass_type(**self._state)

    def set_environment(self, raw: Mapping[str, Any]) -> None:
        """Coerce *raw* and merge it on top of the current state.

        Later calls override values set by earlier calls for the same
        keys.  This allows layering multiple sources (e.g. ``os.environ``
        first, then a secret manager) with deterministic precedence::

            set_environment(os.environ)  # base layer
            set_environment(secret_manager_dict)  # overrides base
            set_environment(os.environ)  # overrides secrets again
        """
        coerced = to_dataclass_dict(self._dataclass_type, raw)
        self._state = {**self._state, **coerced}

    def load(self, raw: Mapping[str, Any]) -> None:
        """Validate mandatory keys in *raw*, then delegate to :meth:`set_environment`.

        Use this for data sources (e.g. AWS Secrets Manager) where certain
        keys are required for the application to function.
        """
        validate_keys(raw, self._mandatory_keys)
        self.set_environment(raw)
