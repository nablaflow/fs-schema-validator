from pathlib import Path

import pytest

from fs_schema_validator import Schema
from fs_schema_validator.report import ValidationError

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_ok(schema: Schema, tmp_path: Path) -> None:
    (tmp_path / "image.png").symlink_to(FIXTURES_DIR / "image.png")
    (tmp_path / "image.webp").symlink_to(FIXTURES_DIR / "image.webp")
    (tmp_path / "image.jpg").symlink_to(FIXTURES_DIR / "image.jpg")
    (tmp_path / "image.svg").symlink_to(FIXTURES_DIR / "image.svg")

    assert schema.validate_(root_dir=tmp_path).errors == []


def test_missing(schema: Schema, tmp_path: Path) -> None:
    assert schema.validate_(root_dir=tmp_path).errors == [
        ValidationError(path=Path("image.png"), reason="does not exist"),
        ValidationError(path=Path("image.webp"), reason="does not exist"),
        ValidationError(path=Path("image.jpg"), reason="does not exist"),
        ValidationError(path=Path("image.svg"), reason="does not exist"),
    ]


def test_fail(schema: Schema, tmp_path: Path) -> None:
    (tmp_path / "image.png").symlink_to(FIXTURES_DIR / "image.webp")
    (tmp_path / "image.webp").symlink_to(FIXTURES_DIR / "image.jpg")
    (tmp_path / "image.jpg").symlink_to(FIXTURES_DIR / "image.png")
    (tmp_path / "image.svg").symlink_to(FIXTURES_DIR / "image.png")

    assert schema.validate_(root_dir=tmp_path).errors == [
        ValidationError(
            path=Path("image.png"), reason="image is not in png format (got webp)"
        ),
        ValidationError(
            path=Path("image.webp"), reason="image is not in webp format (got jpeg)"
        ),
        ValidationError(
            path=Path("image.jpg"), reason="image is not in jpeg format (got png)"
        ),
        ValidationError(
            path=Path("image.svg"), reason="file does not contain a valid svg"
        ),
    ]


@pytest.fixture
def schema() -> Schema:
    return Schema.from_yaml(
        """
      schema:
        - type: image
          format: png
          path: image.png
        - type: image
          format: webp
          path: image.webp
        - type: image
          format: jpeg
          path: image.jpg
        - type: image
          format: svg
          path: image.svg
    """
    )
