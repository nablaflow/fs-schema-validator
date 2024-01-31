from fs_schema_validator.evaluator.values import Binding, Enum, Expansion, Range


def test_expansion_str() -> None:
    assert str(Expansion(Range(0, 10), format="foo")) == "{0..10:foo}"
    assert str(Expansion(Binding("foo"), format="bar")) == "{$foo:bar}"
    assert str(Expansion(Enum({"foo", "bar"}), format="baz")) == "{bar|foo:baz}"
