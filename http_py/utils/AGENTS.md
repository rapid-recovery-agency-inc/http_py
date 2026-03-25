# Utils Module

## Purpose

The `http_py.utils` module contains shared, dependency-light helpers used across packages.
It currently provides:

- boolean normalization (`to_boolean_string`)
- runtime protocol conformance validation (`protocol_conformance_errors`, `conforms_to_protocol`, `assert_conforms_to_protocol`)

## Internal Design

### Protocol validation flow

1. `_validate_protocol_type` enforces that the provided type is both a `Protocol` and `@runtime_checkable`.
2. `_collect_required_protocol_members` collects required attributes and methods from the protocol MRO.
3. `protocol_conformance_errors` checks presence/callability and returns human-readable error strings.
4. `conforms_to_protocol` exposes a bool-only API for guard checks.
5. `assert_conforms_to_protocol` raises `TypeError` with a variable-aware message for fail-fast behavior.

## Conventions

- Keep helpers pure and side-effect free.
- Avoid adding heavyweight dependencies to this module.
- Prefer explicit errors over silent coercion.
- Add tests in `http_py/utils/tests/` for every new helper.

## Testing

- Runtime protocol helper tests live in `http_py/utils/tests/test_protocol_conformance.py`.
- Use `python -m unittest http_py.utils.tests.test_protocol_conformance` for focused validation.
