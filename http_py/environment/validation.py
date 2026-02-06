"""Validation helpers for environment dictionaries."""

from typing import Any
from collections.abc import Mapping


def validate_keys(data: Mapping[str, Any], mandatory_keys: list[str]) -> None:
    """Raise ``ValueError`` if *data* is missing any of the *mandatory_keys*.

    Args:
        data: The dictionary to validate.
        mandatory_keys: Keys that **must** be present in *data*.

    Raises:
        ValueError: Lists every missing key in the error message.
    """
    missing = [k for k in mandatory_keys if k not in data]
    if missing:
        msg = (
            "Environment is missing mandatory keys: "
            f"{', '.join(missing)}"
        )
        raise ValueError(msg)
