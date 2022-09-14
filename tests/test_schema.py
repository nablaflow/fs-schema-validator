from pathlib import Path

import orjson
import pytest

from fs_schema_validator import Schema, ValidationError


@pytest.fixture
def simple_schema() -> Schema:
    return Schema.from_yaml(
        """
      schema:
        - type: png
          path: foo.png
        - type: json
          path: bar.json
          keys:
            - foo
            - bar
            - baz
    """
    )


def test_empty_schema_ok(tmp_path: Path) -> None:
    schema = Schema.from_yaml(
        """
      schema: []
    """
    )
    assert schema.validate_(root_dir=tmp_path).errors == []


def test_simple_schema_fail(simple_schema: Schema, tmp_path: Path) -> None:
    assert simple_schema.validate_(root_dir=tmp_path).errors == [
        ValidationError(path=Path("foo.png"), reason="does not exist"),
        ValidationError(path=Path("bar.json"), reason="does not exist"),
    ]


def test_simple_schema_ok(simple_schema: Schema, tmp_path: Path) -> None:
    png_path = tmp_path / "foo.png"
    png_path.write_bytes(bytes())

    json_path = tmp_path / "bar.json"
    json_path.write_bytes(orjson.dumps({"foo": 1, "bar": 2, "baz": 3}))

    assert simple_schema.validate_(root_dir=tmp_path).errors == []
