import pytest

from fs_schema_validator.string_expander.parser import (
    ParseError,
    parse_assignment,
    parse_template,
)
from fs_schema_validator.string_expander.values import Binding, Enum, Range, String


def test_template() -> None:
    assert [
        String("foo-"),
        Enum({"bar", "baz"}),
        String("-"),
        Range(0, 10),
        String(".jpg"),
    ] == parse_template("foo-{bar|baz}-{0..10}.jpg")


def test_template_fail() -> None:
    with pytest.raises(ParseError):
        parse_template("")

    with pytest.raises(ParseError):
        parse_template("foo-{{foo|bar}}")


def test_enum() -> None:
    assert [Enum({"foo"})] == parse_template("{foo}")
    assert [Enum({"+"})] == parse_template("{+}")
    assert [Enum({"-"})] == parse_template("{-}")
    assert [Enum({"_"})] == parse_template("{_}")
    assert [Enum({"foo", "bar"})] == parse_template("{foo|bar}")
    assert [Enum({"foo", "bar"})] == parse_template("{ foo | bar }")
    assert [Enum({"foo2"})] == parse_template("{foo2}")

    assert [Enum({"foo", ""})] == parse_template("{foo|}")
    assert [Enum({"foo", ""})] == parse_template("{ foo | }")
    assert [Enum({""})] == parse_template("{ | }")
    assert [Enum({""})] == parse_template("{|}")
    assert [Enum({""})] == parse_template("{}")

    assert [Enum({"20.."})] == parse_template("{20..}")
    assert [Enum({"..30"})] == parse_template("{..30}")


def test_range() -> None:
    assert [Range(0, 10)] == parse_template("{0..10}")
    assert [Range(20, 100)] == parse_template("{20..100}")
    assert [Range(-4, 100)] == parse_template("{-4..100}")


def test_binding() -> None:
    assert [Binding("foo")] == parse_template("{$foo}")


def test_binding_fail() -> None:
    with pytest.raises(ParseError):
        parse_template("{$0}")

    with pytest.raises(ParseError):
        parse_template("{$-}")


def test_assignment() -> None:
    assert ("foo", Range(0, 1)) == parse_assignment("foo=0..1")
    assert ("foo", Enum({"bar", "baz"})) == parse_assignment("foo=bar|baz")
    assert ("foo", Enum({".393123j"})) == parse_assignment("foo=.393123j")
    assert ("foo", Enum({"1234"})) == parse_assignment("foo=1234")
    assert ("foo", Enum({""})) == parse_assignment("foo=")


def test_assignment_fail() -> None:
    with pytest.raises(ParseError):
        parse_assignment("foo")

    with pytest.raises(ParseError):
        parse_assignment("foo={}")
