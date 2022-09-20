from fs_schema_validator.string_expander.values import (
    Binding,
    Enum,
    Expansion,
    Range,
    String,
)


def test_expansion_str() -> None:
    assert "{0..10:foo}" == str(Expansion(Range(0, 10), format="foo"))
    assert "{$foo:bar}" == str(Expansion(Binding("foo"), format="bar"))
    assert "{bar|foo:baz}" == str(Expansion(Enum({"foo", "bar"}), format="baz"))
