from pathlib import Path

from fs_schema_validator import Schema


def test_empty_schema_ok(tmp_path: Path) -> None:
    schema = Schema.from_yaml(
        """
      schema: []
    """
    )
    assert schema.validate_(root_dir=tmp_path).errors == []
