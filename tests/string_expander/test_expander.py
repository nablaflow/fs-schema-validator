import pytest

from fs_schema_validator.string_expander import expand
from fs_schema_validator.string_expander.errors import UnboundSymbol
from fs_schema_validator.string_expander.values import Enum, Range


def test_without_placeholders() -> None:
    assert {"foo"} == set(expand("foo"))


def test_enum_placeholder() -> None:
    assert {"foo-bar"} == set(expand("foo-{bar}"))
    assert {"foo-bar", "foo-baz"} == set(expand("foo-{bar|baz}"))


def test_escaping() -> None:
    assert {"foo-{6}"} == set(expand("foo-{{6}}"))


def test_range_placeholder() -> None:
    assert {"foo-0", "foo-1", "foo-2", "foo-3", "foo-4", "foo-5"} == set(
        expand("foo-{0..5}")
    )


def test_full() -> None:
    assert {
        "foo-bar-0.jpg",
        "foo-bar-1.jpg",
        "foo-bar-2.jpg",
        "foo-baz-0.jpg",
        "foo-baz-1.jpg",
        "foo-baz-2.jpg",
    } == set(expand("foo-{bar|baz}-{0..2}.jpg"))


def test_params() -> None:
    assert {
        "foo-bar-0.jpg",
        "foo-bar-1.jpg",
        "foo-bar-2.jpg",
        "foo-baz-0.jpg",
        "foo-baz-1.jpg",
        "foo-baz-2.jpg",
    } == set(
        expand(
            "foo-{$foo}-{$bar}.jpg",
            {
                "foo": Enum({"bar", "baz"}),
                "bar": Range(0, 2),
            },
        )
    )


def test_params_fail() -> None:
    with pytest.raises(UnboundSymbol):
        expand("foo-{$foo}-{$bar}.jpg")


def test_leave_unbound_bindings() -> None:
    assert {
        "foo-{$baz:02}.jpg",
        "bar-{$baz:02}.jpg",
    } == set(expand("{foo|bar}-{$baz:02}.jpg", leave_unbound_vars_in=True))
