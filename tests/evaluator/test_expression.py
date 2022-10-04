import pytest

from fs_schema_validator.evaluator import evaluate
from fs_schema_validator.evaluator.errors import UnboundSymbol
from fs_schema_validator.evaluator.values import String


def test_boolean_expressions() -> None:
    assert True == evaluate("$foo == bar", {"foo": String("bar")})
    assert False == evaluate("$foo == bar", {"foo": String("foo")})

    assert False == evaluate("$foo != bar", {"foo": String("bar")})
    assert True == evaluate("$foo != bar", {"foo": String("foo")})


def test_missing_bindings() -> None:
    with pytest.raises(UnboundSymbol):
        evaluate("$foo == bar")
