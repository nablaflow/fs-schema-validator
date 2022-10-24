import pytest

from fs_schema_validator.evaluator import evaluate
from fs_schema_validator.evaluator.errors import CoercionError, UnboundSymbol
from fs_schema_validator.evaluator.values import Enum, Range, String


def test_boolean_expressions() -> None:
    assert True == evaluate("$foo == bar", {"foo": String("bar")})
    assert False == evaluate("$foo == bar", {"foo": String("foo")})

    assert False == evaluate("$foo != bar", {"foo": String("bar")})
    assert True == evaluate("$foo != bar", {"foo": String("foo")})

    assert False == evaluate("$foo != bar", {"foo": Enum({"bar"})})
    assert True == evaluate("$foo != bar", {"foo": Enum({"foo"})})


def test_missing_bindings() -> None:
    with pytest.raises(UnboundSymbol):
        evaluate("$foo == bar")


def test_cannot_coerce_range() -> None:
    with pytest.raises(CoercionError):
        evaluate("$foo == bar", {"foo": Range(1, 10)})


def test_cannot_coerce_enum_with_more_than_one_variant() -> None:
    with pytest.raises(CoercionError):
        evaluate("$foo == bar", {"foo": Enum({"foo", "bar"})})
