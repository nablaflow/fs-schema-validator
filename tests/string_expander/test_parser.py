import pytest

from fs_schema_validator.string_expander.parser import (
    ParseError,
    parse_assignment,
    parse_template,
)
from fs_schema_validator.string_expander.values import (
    Binding,
    Enum,
    Expansion,
    Range,
    String,
)


def test_template() -> None:
    assert [
        String("foo-"),
        Expansion(Enum({"bar", "baz"})),
        String("-"),
        Expansion(Range(0, 10)),
        String(".jpg"),
    ] == parse_template("foo-{bar|baz}-{0..10}.jpg")


def test_double_parenthesis_are_strings() -> None:
    assert [String("foo-"), String("{6}")] == parse_template("foo-{{6}}")


def test_empty_string() -> None:
    assert [String("")] == parse_template("")


def test_enum() -> None:
    assert [Expansion(Enum({"foo"}))] == parse_template("{foo}")
    assert [Expansion(Enum({"+"}))] == parse_template("{+}")
    assert [Expansion(Enum({"-"}))] == parse_template("{-}")
    assert [Expansion(Enum({"_"}))] == parse_template("{_}")
    assert [Expansion(Enum({"foo", "bar"}))] == parse_template("{foo|bar}")
    assert [Expansion(Enum({"foo", "bar"}))] == parse_template("{ foo | bar }")
    assert [Expansion(Enum({"foo2"}))] == parse_template("{foo2}")

    assert [Expansion(Enum({"foo", ""}))] == parse_template("{foo|}")
    assert [Expansion(Enum({"foo", ""}))] == parse_template("{ foo | }")
    assert [Expansion(Enum({""}))] == parse_template("{ | }")
    assert [Expansion(Enum({""}))] == parse_template("{|}")
    assert [Expansion(Enum({""}))] == parse_template("{}")

    assert [Expansion(Enum({"20.."}))] == parse_template("{20..}")
    assert [Expansion(Enum({"..30"}))] == parse_template("{..30}")


def test_enum_with_range() -> None:
    assert [Expansion(Enum({"foo"}), format=">5")] == parse_template("{foo:>5}")


def test_range() -> None:
    assert [Expansion(Range(0, 10))] == parse_template("{0..10}")
    assert [Expansion(Range(20, 100))] == parse_template("{20..100}")
    assert [Expansion(Range(-4, 100))] == parse_template("{-4..100}")


def test_range_with_format() -> None:
    assert [Expansion(Range(0, 10), format="02")] == parse_template("{0..10:02}")
    assert [Expansion(Range(20, 100), format="x")] == parse_template("{20..100:x}")


def test_binding() -> None:
    assert [Expansion(Binding("foo"))] == parse_template("{$foo}")


def test_with_format() -> None:
    assert [Expansion(Binding("foo"), format="02")] == parse_template("{$foo:02}")


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
