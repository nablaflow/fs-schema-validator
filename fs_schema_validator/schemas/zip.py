from pathlib import Path
from typing import Literal
from zipfile import BadZipFile, ZipFile

from pydantic import BaseModel

from fs_schema_validator.evaluator.values import Bindings
from fs_schema_validator.report import ValidationReport
from fs_schema_validator.utils import _assert_path_exists


class ZipSchema(BaseModel):
    type: Literal["zip"]
    path: Path

    def inner_bindings(self) -> Bindings:
        return {}

    def validate_(self, root_dir: Path, report: ValidationReport) -> bool:
        if not _assert_path_exists(root_dir, self.path, report):
            return False

        try:
            with (root_dir / self.path).open("rb") as f, ZipFile(f) as zip:
                if zip.testzip() is not None:
                    report.append(path=self.path, reason="crc checks failed")
                    return False
        except BadZipFile as ex:
            report.append(path=self.path, reason=str(ex))
            return False

        return True
