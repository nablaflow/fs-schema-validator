from enum import Enum, unique
from pathlib import Path
from typing import Literal

import pillow_avif  # noqa: F401
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel
from svglib import svglib

from fs_schema_validator.evaluator.values import Bindings, String
from fs_schema_validator.report import ValidationReport
from fs_schema_validator.utils import _assert_path_exists


@unique
class ImageFormat(Enum):
    PNG = "png"
    WEBP = "webp"
    JPEG = "jpeg"
    SVG = "svg"
    TIFF = "tiff"
    AVIF = "avif"

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

        if self.format is ImageFormat.SVG:
            return self._validate_svg(root_dir, report)

        return self._validate_raster(root_dir, report)

    def _validate_svg(self, root_dir: Path, report: ValidationReport) -> bool:
        if svglib.load_svg_file(root_dir / self.path) is None:
            report.append(path=self.path, reason="file does not contain a valid svg")
            return False

        return True

    def _validate_raster(self, root_dir: Path, report: ValidationReport) -> bool:
        try:
            with Image.open(root_dir / self.path) as im:
                if im.format is None:
                    report.append(
                        path=self.path,
                        reason=f"image is not in {self.format.value} format (unknown format detected)",
                    )
                    return False

                if im.format != self.format.to_pillow_format():
                    report.append(
                        path=self.path,
                        reason=f"image is not in {self.format.value} format (got {im.format.lower()})",
                    )
                    return False
        except UnidentifiedImageError:
            report.append(path=self.path, reason="file does not contain a valid image")
            return False

        return True
