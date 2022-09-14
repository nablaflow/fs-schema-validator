from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from fs_schema_validator.report import ValidationError, ValidationReport
from fs_schema_validator.utils import _assert_path_exists


class PngSchema(BaseModel):
    type: Literal["png"]
    path: Path

    def validate_(self, root_dir: Path, report: ValidationReport) -> None:
        _assert_path_exists(root_dir, self.path, report)
