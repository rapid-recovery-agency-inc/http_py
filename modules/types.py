from typing import Literal


BooleanString = Literal["true", "false"]


def to_boolean_string(value: bool | int | str) -> BooleanString:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return "true" if value == 1 else "false"
    if isinstance(value, str):
        lower_cased = value.lower()
        if lower_cased == "true":
            return "true"
        if lower_cased == "false":
            return "false"
    raise ValueError(f"Expected bool, int, or str, got {type(value)}")
