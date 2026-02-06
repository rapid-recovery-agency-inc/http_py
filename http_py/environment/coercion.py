"""Generic type coercion utilities for environment values.

Converts raw string values (typically from os.environ or secret managers)
into the types declared on a frozen dataclass.
"""

import json
import inspect
import dataclasses
from enum import Enum
from typing import Any, get_type_hints
from collections.abc import Mapping


def convert_value(expected_type: type, value: Any) -> Any:  # noqa: PLR0912, PLR0911, C901
    """Convert a raw value to the expected type.

    Handles: str, bool, int, float, list, set, tuple, dict, Enum subclasses,
    and any Literal type (returned as-is after passing through a user-supplied
    converter registered via the `converters` dict on the dataclass field).

    Args:
        expected_type: The target type to coerce *value* into.
        value: The raw value (usually a ``str`` from the environment).

    Returns:
        The coerced value.

    Raises:
        ValueError: When *value* cannot be converted.
    """
    if expected_type is str:
        if isinstance(value, str):
            return value
        return str(value)

    if expected_type is bool:
        if isinstance(value, bool):
            return value
        return value.lower() == "true"

    if expected_type is int:
        return int(value)

    if expected_type is float:
        return float(value)

    if expected_type is list:
        if isinstance(value, list):
            return value  # type: ignore[return-value]
        if isinstance(value, str):
            return value.split(",")
        raise ValueError(f"Expected list or str, got {type(value)}")

    if expected_type in (set, tuple):
        if isinstance(value, expected_type):
            return value  # type: ignore[return-value]
        return value.split(",")

    if expected_type is dict:
        return json.loads(value)

    if inspect.isclass(expected_type):
        if issubclass(expected_type, Enum):
            return expected_type[value]

    # Fall-through: Literal types, custom aliases, etc. — return as-is.
    return value


def to_dataclass_dict(
    dataclass_type: type,
    raw: Mapping[str, Any],
) -> dict[str, Any]:
    """Filter and coerce *raw* into a dict whose keys/types match *dataclass_type*.

    Only keys that correspond to fields on *dataclass_type* are kept.
    Each value is coerced via :func:`convert_value`, unless the field
    declares a custom converter in its metadata::

        @dataclass(frozen=True)
        class MyEnv:
            SOME_FLAG: BooleanString = field(
                default="false",
                metadata={"converter": to_boolean_string},
            )

    When a ``"converter"`` key is present in ``field.metadata``, that
    callable is used instead of the default :func:`convert_value`.

    Args:
        dataclass_type: A frozen ``@dataclass`` class whose fields define the
            valid keys and their expected types.
        raw: The raw key/value mapping (e.g. ``os.environ``).

    Returns:
        A dict ready to be unpacked into ``dataclass_type(**result)``.
    """
    fields = dataclasses.fields(dataclass_type)
    type_hints = get_type_hints(dataclass_type)

    # Build a lookup of field-level converters from metadata.
    field_converters: dict[str, Any] = {}
    valid_field_names: set[str] = set()
    for f in fields:
        valid_field_names.add(f.name)
        converter = f.metadata.get("converter") if f.metadata else None
        if converter is not None:
            field_converters[f.name] = converter

    result: dict[str, Any] = {}
    for key in valid_field_names:
        maybe_value = raw.get(key)
        if maybe_value is not None:
            if key in field_converters:
                result[key] = field_converters[key](maybe_value)
            else:
                result[key] = convert_value(type_hints[key], maybe_value)
    return result
