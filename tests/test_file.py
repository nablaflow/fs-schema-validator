from pathlib import Path

from fs_schema_validator import Schema
from fs_schema_validator.report import ValidationError


def test_ok(tmp_path: Path) -> None:
    json_path = tmp_path / "file.txt"
    json_path.write_bytes(b"foo")

    schema = Schema.from_yaml(
        """
      schema:
        - type: file
          path: file.txt
    """
    )

    assert schema.validate_(root_dir=tmp_path).errors == []


def test_empty_fail(tmp_path: Path) -> None:
    json_path = tmp_path / "file.txt"
    json_path.write_bytes(b"")

    schema = Schema.from_yaml(
        """
      schema:
        - type: file
          path: file.txt
    """
    )

    assert set(schema.validate_(root_dir=tmp_path).errors) == {
        ValidationError(path=Path("file.txt"), reason="cannot be empty")
    }


def test_empty_ok(tmp_path: Path) -> None:
    json_path = tmp_path / "file.txt"
    json_path.write_bytes(b"")

    schema = Schema.from_yaml(
        """
      schema:
        - type: file
          path: file.txt
          allow_empty: true
    """
    )

    assert schema.validate_(root_dir=tmp_path).errors == []
