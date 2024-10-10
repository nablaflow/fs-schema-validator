from pathlib import Path
from zipfile import ZipFile

from fs_schema_validator import Schema
from fs_schema_validator.report import ValidationError


def test_ok(tmp_path: Path) -> None:
    zip_path = tmp_path / "file.zip"

    with zip_path.open("wb") as f, ZipFile(f, mode="w") as zip:
        zip.writestr("foo.txt", "bar")

    schema = Schema.from_yaml(
        """
      schema:
        - type: zip
          path: file.zip
    """
    )

    assert schema.validate_(root_dir=tmp_path).errors == []


def test_ko(tmp_path: Path) -> None:
    zip_path = tmp_path / "file.zip"
    zip_path.write_text("lol")

    schema = Schema.from_yaml(
        """
      schema:
        - type: zip
          path: file.zip
    """
    )

    assert schema.validate_(root_dir=tmp_path).errors == [
        ValidationError(path=Path("file.zip"), reason="File is not a zip file"),
    ]
