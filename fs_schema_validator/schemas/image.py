from enum import Enum, unique
from pathlib import Path
from typing import Literal

from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel

from fs_schema_validator.report import ValidationReport
from fs_schema_validator.string_expander.values import Bindings, String
from fs_schema_validator.utils import _assert_path_exists


@unique
class ImageFormat(Enum):
    PNG = "png"
    WEBP = "webp"
    JPEG = "jpeg"

    def to_pillow_format(self) -> str:
        return self.value.upper()


class ImageSchema(BaseModel):
    type: Literal["image"]
    format: ImageFormat
    path: Path

    def inner_bindings(self) -> Bindings:
        return {
            "format": String(self.format.value),
        }

    def validate_(self, root_dir: Path, report: ValidationReport) -> bool:
        if not _assert_path_exists(root_dir, self.path, report):
            return False

        try:
            with Image.open(root_dir / self.path) as im:
                if im.format is None:
                    report.append(
                        path=self.path,
                        reason=f"image is not in {self.format.value} format (unknown format detected)",
                    )
                    return False
                elif im.format != self.format.to_pillow_format():
                    report.append(
                        path=self.path,
                        reason=f"image is not in {self.format.value} format (got {im.format.lower()})",
                    )
                    return False
        except UnidentifiedImageError:
            report.append(path=self.path, reason="file does not contain a valid image")
            return False

        return True
