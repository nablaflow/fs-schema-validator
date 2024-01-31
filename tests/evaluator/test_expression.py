import pytest

from fs_schema_validator.evaluator import evaluate
from fs_schema_validator.evaluator.errors import CoercionError, UnboundSymbolError
from fs_schema_validator.evaluator.values import Enum, Range, String


def test_boolean_expressions() -> None:
    assert evaluate("$foo == bar", {"foo": String("bar")}) is True
    assert evaluate("$foo == bar", {"foo": String("foo")}) is False

    assert evaluate("$foo != bar", {"foo": String("bar")}) is False
    assert evaluate("$foo != bar", {"foo": String("foo")}) is True

    assert evaluate("$foo != bar", {"foo": Enum({"bar"})}) is False
    assert evaluate("$foo != bar", {"foo": Enum({"foo"})}) is True


def test_missing_bindings() -> None:
    with pytest.raises(UnboundSymbolError):
        evaluate("$foo == bar")


def test_cannot_coerce_range() -> None:
    with pytest.raises(CoercionError):
        evaluate("$foo == bar", {"foo": Range(1, 10)})


def test_cannot_coerce_enum_with_more_than_one_variant() -> None:
    with pytest.raises(CoercionError):
        evaluate("$foo == bar", {"foo": Enum({"foo", "bar"})})
