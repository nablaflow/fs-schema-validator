from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from fs_schema_validator.evaluator.values import Bindings
from fs_schema_validator.report import ValidationReport
from fs_schema_validator.utils import _assert_path_exists


class FileSchema(BaseModel):
    type: Literal["file"]
    path: Path
    allow_empty: bool = False

    def inner_bindings(self) -> Bindings:
        return {}

    def validate_(self, root_dir: Path, report: ValidationReport) -> bool:
        if not _assert_path_exists(root_dir, self.path, report):
            return False

        if not self.allow_empty and self._file_size(root_dir) == 0:
            report.append(path=self.path, reason="cannot be empty")

        return True

    def _file_size(self, root_dir: Path) -> int:
        return (root_dir / self.path).stat().st_size
