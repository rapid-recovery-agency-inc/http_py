from typing import Literal


def _validate_protocol_type(protocol: type[object]) -> None:
    if not getattr(protocol, "_is_protocol", False):
        msg = f"Expected a Protocol type, got {protocol!r}"
        raise TypeError(msg)
    if not getattr(protocol, "_is_runtime_protocol", False):
        msg = (
            f"Protocol {protocol.__name__} must be decorated with @runtime_checkable "
            "for runtime conformance checks"
        )
        raise TypeError(msg)


def _collect_required_protocol_members(
    protocol: type[object],
) -> tuple[set[str], set[str]]:
    required_attributes: set[str] = set()
    required_methods: set[str] = set()

    for base in reversed(protocol.__mro__):
        if not getattr(base, "_is_protocol", False):
            continue

        required_attributes.update(getattr(base, "__annotations__", {}).keys())

        for name, member in base.__dict__.items():
            if name.startswith("_"):
                continue
            if isinstance(member, property):
                required_attributes.add(name)
                continue
            if callable(member):
                required_methods.add(name)

    return required_attributes, required_methods


def protocol_conformance_errors(value: object, protocol: type[object]) -> list[str]:
    _validate_protocol_type(protocol)

    required_attributes, required_methods = _collect_required_protocol_members(protocol)
    errors: list[str] = []

    for attribute in sorted(required_attributes):
        if not hasattr(value, attribute):
            errors.append(f"missing attribute '{attribute}'")

    for method in sorted(required_methods):
        if not hasattr(value, method):
            errors.append(f"missing method '{method}'")
            continue
        candidate = getattr(value, method)
        if not callable(candidate):
            errors.append(f"member '{method}' is not callable")

    return errors


def conforms_to_protocol(value: object, protocol: type[object]) -> bool:
    return len(protocol_conformance_errors(value, protocol)) == 0


def assert_conforms_to_protocol(
    value: object,
    protocol: type[object],
    *,
    variable_name: str = "value",
) -> None:
    errors = protocol_conformance_errors(value, protocol)
    if errors:
        joined_errors = ", ".join(errors)
        msg = (
            f"{variable_name} does not conform to protocol {protocol.__name__}: "
            f"{joined_errors}"
        )
        raise TypeError(msg)


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
