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


def test_variable_expansion(tmp_path: Path) -> None:
    schema = Schema.from_yaml(
        """
      bindings:
        range: [0, 2]
        enum:
          - bar
          - baz
      schema:
        - type: image
          format: png
          path: foo-{$enum}-{$range}.png
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
