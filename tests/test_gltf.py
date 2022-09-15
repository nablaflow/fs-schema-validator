from pathlib import Path

import pytest

from fs_schema_validator import Schema
from fs_schema_validator.report import ValidationError

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_ok(schema: Schema, tmp_path: Path) -> None:
    (tmp_path / "asset.glb").symlink_to(FIXTURES_DIR / "asset.glb")
    (tmp_path / "asset.gltf").symlink_to(FIXTURES_DIR / "asset.gltf")

    assert schema.validate_(root_dir=tmp_path).errors == []


def test_missing(schema: Schema, tmp_path: Path) -> None:
    assert schema.validate_(root_dir=tmp_path).errors == [
        ValidationError(path=Path("asset.glb"), reason="does not exist"),
        ValidationError(path=Path("asset.gltf"), reason="does not exist"),
    ]


def test_fail(schema: Schema, tmp_path: Path) -> None:
    (tmp_path / "asset.glb").symlink_to(FIXTURES_DIR / "corrupted.glb")
    (tmp_path / "asset.gltf").symlink_to(FIXTURES_DIR / "corrupted.gltf")

    assert schema.validate_(root_dir=tmp_path).errors == [
        ValidationError(
            path=Path("asset.glb"),
            reason="failed to deserialize: (<class 'struct.error'>) unpack requires a buffer of 8 bytes",
        ),
        ValidationError(
            path=Path("asset.gltf"),
            reason="failed to deserialize: (<class 'json.decoder.JSONDecodeError'>) Unterminated string starting at: line 2 column 4 (char 5)",
        ),
    ]


def test_fail_empty_nodes(schema: Schema, tmp_path: Path) -> None:
    (tmp_path / "asset.gltf").write_text("{}")

    assert (
        ValidationError(path=Path("asset.gltf"), reason="file does not contain nodes")
        in schema.validate_(root_dir=tmp_path).errors
    )


@pytest.fixture
def schema() -> Schema:
    return Schema.from_yaml(
        """
      schema:
        - type: gltf
          format: glb
          path: asset.glb
        - type: gltf
          format: gltf
          path: asset.gltf
    """
    )
