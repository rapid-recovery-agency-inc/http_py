from typing import Protocol, runtime_checkable

import pytest

from http_py.utils.protocols import (
    conforms_to_protocol,
    assert_conforms_to_protocol,
    protocol_conformance_errors,
)


@runtime_checkable
class ExampleProtocol(Protocol):
    name: str

    def run(self) -> str: ...


class ValidExample:
    name = "worker"

    def run(self) -> str:
        return "ok"


class MissingMethodExample:
    name = "worker"


class NotCallableMethodExample:
    name = "worker"
    run = "not-a-method"


def test_conforms_to_protocol_true_for_valid_value() -> None:
    assert conforms_to_protocol(ValidExample(), ExampleProtocol)


def test_conforms_to_protocol_false_when_method_missing() -> None:
    assert not conforms_to_protocol(MissingMethodExample(), ExampleProtocol)


def test_protocol_conformance_errors_reports_missing_method() -> None:
    errors = protocol_conformance_errors(MissingMethodExample(), ExampleProtocol)
    assert "missing method 'run'" in errors


def test_protocol_conformance_errors_reports_not_callable() -> None:
    errors = protocol_conformance_errors(
        NotCallableMethodExample(),
        ExampleProtocol,
    )
    assert "member 'run' is not callable" in errors


def test_assert_conforms_to_protocol_raises_with_variable_name() -> None:
    with pytest.raises(
        TypeError,
        match="env does not conform to protocol ExampleProtocol: missing method 'run'",
    ):
        assert_conforms_to_protocol(
            MissingMethodExample(),
            ExampleProtocol,
            variable_name="env",
        )


def test_assert_conforms_to_protocol_with_non_protocol_raises() -> None:
    with pytest.raises(TypeError, match="Expected a Protocol type"):
        assert_conforms_to_protocol(ValidExample(), dict)


def test_assert_conforms_to_protocol_with_non_runtime_protocol_raises() -> None:
    class NonRuntimeProtocol(Protocol):
        name: str

    with pytest.raises(
        TypeError,
        match="must be decorated with @runtime_checkable",
    ):
        assert_conforms_to_protocol(ValidExample(), NonRuntimeProtocol)
