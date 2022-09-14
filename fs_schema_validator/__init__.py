import itertools
import typing
from io import IOBase
from pathlib import Path
from typing import Dict, Iterator, List, Literal, Tuple, Union

import orjson
import yaml
from pydantic import BaseModel, Field

if typing.TYPE_CHECKING:
    from _typeshed import SupportsRead


class ValidationError(BaseModel):
    path: Path
    reason: str

    @staticmethod
    def missing_path(path: Path) -> "ValidationError":
        return ValidationError(path=path, reason="does not exist")


class ValidationReport(BaseModel):
    errors: List[ValidationError] = []

    def grouped_by_path(self) -> Iterator[Tuple[Path, List[str]]]:
        return map(
            lambda a: (a[0], list(map(lambda e: e.reason, a[1]))),
            itertools.groupby(
                sorted(self.errors, key=lambda e: e.path), lambda e: e.path
            ),
        )


def _assert_path_exists(root_dir: Path, path: Path, report: ValidationReport) -> bool:
    if not (root_dir / path).exists():
        report.errors.append(ValidationError.missing_path(path))
        return False

    return True


class JsonSchema(BaseModel):
    type: Literal["json"]
    path: Path
    keys: List[str]

    def validate_(self, root_dir: Path, report: ValidationReport) -> None:
        if not _assert_path_exists(root_dir, self.path, report):
            return

        with (root_dir / self.path).open() as f:
            try:
                json = orjson.loads(f.read())
            except orjson.JSONDecodeError as e:
                report.errors.append(
                    ValidationError(path=self.path, reason=f"invalid json file, {e}")
                )

            for key in self.keys:
                if not key in json:
                    report.errors.append(
                        ValidationError(path=self.path, reason=f"key `{key}` is missing")
                    )


class PngSchema(BaseModel):
    type: Literal["png"]
    path: Path

    def validate_(self, root_dir: Path, report: ValidationReport) -> None:
        _assert_path_exists(root_dir, self.path, report)


class Schema(BaseModel):
    validators: List[Union[JsonSchema, PngSchema]] = Field(alias="schema")

    @staticmethod
    def from_yaml(
        f: Union[str, bytes, "SupportsRead[str]", "SupportsRead[bytes]"]
    ) -> "Schema":
        return Schema(**yaml.safe_load(f))

    def validate_(self, root_dir: Path) -> ValidationReport:
        report = ValidationReport()

        for validator in self.validators:
            validator.validate_(root_dir, report)

        return report
