from pathlib import Path

from fs_schema_validator import Schema
from fs_schema_validator.report import ValidationError


def test_empty_schema_ok(tmp_path: Path) -> None:
    schema = Schema.from_yaml(
        """
      schema: []
    """
    )
    assert schema.validate_(root_dir=tmp_path).errors == []


def test_expansion(tmp_path: Path) -> None:
    schema = Schema.from_yaml(
        """
      schema:
        - type: image
          format: png
          path: foo-{bar|baz}.png
    """
    )
    assert set(schema.validate_(root_dir=tmp_path).errors) == {
        ValidationError(path=Path("foo-bar.png"), reason="does not exist"),
        ValidationError(path=Path("foo-baz.png"), reason="does not exist"),
    }


def test_range_expansion_with_format(tmp_path: Path) -> None:
    schema = Schema.from_yaml(
        """
      schema:
        - type: image
          format: png
          path: foo-{0..2:02}.png
    """
    )
    assert set(schema.validate_(root_dir=tmp_path).errors) == {
        ValidationError(path=Path("foo-00.png"), reason="does not exist"),
        ValidationError(path=Path("foo-01.png"), reason="does not exist"),
        ValidationError(path=Path("foo-02.png"), reason="does not exist"),
    }


def test_enum_expansion_with_format(tmp_path: Path) -> None:
    schema = Schema.from_yaml(
        """
      schema:
        - type: image
          format: png
          path: foo-{bar|baz:>5}.png
    """
    )
    assert set(schema.validate_(root_dir=tmp_path).errors) == {
        ValidationError(path=Path("foo-  bar.png"), reason="does not exist"),
        ValidationError(path=Path("foo-  baz.png"), reason="does not exist"),
    }


def test_variable_expansion(tmp_path: Path) -> None:
    schema = Schema.from_yaml(
        """
      bindings:
        range: [0, 2]
        enum: [bar, baz]
        string: "foo"
      schema:
        - type: image
          format: png
          path: "{$string}-{$enum}-{$range}.png"
    """
    )
    assert set(schema.validate_(root_dir=tmp_path).errors) == {
        ValidationError(path=Path("foo-bar-0.png"), reason="does not exist"),
        ValidationError(path=Path("foo-bar-1.png"), reason="does not exist"),
        ValidationError(path=Path("foo-bar-2.png"), reason="does not exist"),
        ValidationError(path=Path("foo-baz-0.png"), reason="does not exist"),
        ValidationError(path=Path("foo-baz-1.png"), reason="does not exist"),
        ValidationError(path=Path("foo-baz-2.png"), reason="does not exist"),
    }


def test_expansion_not_in_paths(tmp_path: Path) -> None:
    schema = Schema.from_yaml(
        """
      bindings:
        formats: [webp, png]
      schema:
        - type: image
          format: "{$formats}"
          path: "{foo|bar}.{$format}"
    """
    )
    assert set(schema.validate_(root_dir=tmp_path).errors) == {
        ValidationError(path=Path("foo.webp"), reason="does not exist"),
        ValidationError(path=Path("foo.png"), reason="does not exist"),
        ValidationError(path=Path("bar.webp"), reason="does not exist"),
        ValidationError(path=Path("bar.png"), reason="does not exist"),
    }


def test_if_expression_skip(tmp_path: Path) -> None:
    schema = Schema.from_yaml(
        """
      bindings:
        foo: "bar"
      schema:
        - type: image
          format: png
          path: missing.png
          if: $foo == foo
    """
    )
    assert schema.validate_(root_dir=tmp_path).errors == []


def test_if_expression(tmp_path: Path) -> None:
    schema = Schema.from_yaml(
        """
      bindings:
        foo: "bar"
      schema:
        - type: image
          format: png
          path: missing.png
          if: $foo == bar
    """
    )
    assert schema.validate_(root_dir=tmp_path).errors == [
        ValidationError(path=Path("missing.png"), reason="does not exist"),
    ]
