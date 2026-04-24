"""Generic environment manager bound to a frozen dataclass shape."""

from typing import Any, TypeVar
from collections.abc import Mapping, Callable

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
        post_set_hook: Optional callback invoked after each
            :meth:`set_environment` call.  It receives the newly built
            ``T`` instance and must return a (possibly modified) ``T``
            that becomes the stored state.
    """

    def __init__(
        self,
        dataclass_type: type[T],
        *,
        mandatory_keys: list[str] | None = None,
        post_set_hook: Callable[[T], T] | None = None,
    ) -> None:
        self._dataclass_type = dataclass_type
        self._mandatory_keys = mandatory_keys or []
        self._post_set_hook = post_set_hook
        self._state: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def env(self) -> T:
        """Return a **new** frozen ``T`` instance from the accumulated state."""
        return self._dataclass_type(**self._state)

    def set_environment(
        self,
        raw: Mapping[str, Any],
        validate_values: bool = False,
        prefer_set_values: bool = False,
    ) -> None:
        """Coerce *raw* and merge it on top of the current state.

        By default, newer values replace older ones. When prefer_set_values is
        enabled, any field already set to a non-None value keeps its existing
        value, and only missing fields are filled from ``raw``.

        Args:
            raw: Incoming environment-like mapping to coerce and merge.
            validate_values: Unused legacy flag.
            prefer_set_values: Preserve already-set non-None values in state.

        Examples:
            set_environment(os.environ)  # base layer
            set_environment(secret_manager_dict)  # overrides base
            set_environment(os.environ)  # overrides secrets again

            set_environment(os.environ)  # base layer
            set_environment(os.environ, prefer_set_values=True)  # preserves base values
        """

        coerced = to_dataclass_dict(self._dataclass_type, raw)

        if prefer_set_values:
            # Preserve any already-set, non-None values in the existing state.
            # Only fill keys that are unset or currently None.
            for key, value in coerced.items():
                if self._state.get(key) is None:
                    self._state[key] = value
        else:
            # Default behavior: later calls override earlier values.
            self._state = {**self._state, **coerced}

        if self._post_set_hook is not None:
            instance = self._dataclass_type(**self._state)
            transformed = self._post_set_hook(instance)
            self._state = {**transformed.__dict__}

    def load(self, raw: Mapping[str, Any]) -> None:
        """Validate mandatory keys in *raw*, then delegate to :meth:`set_environment`.

        Use this for data sources (e.g. AWS Secrets Manager) where certain
        keys are required for the application to function.
        """
        validate_keys(raw, self._mandatory_keys)
        self.set_environment(raw)
