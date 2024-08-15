from __future__ import annotations

import itertools
from collections.abc import Iterator
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class ValidationError(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: Path
    reason: str


class ValidationReport(BaseModel):
    errors: list[ValidationError] = Field(default_factory=list)
    valid_paths: list[Path] = Field(default_factory=list)

    def append(self, path: Path, reason: str) -> None:
        self.errors.append(ValidationError(path=path, reason=reason))

    def append_missing_file(self, path: Path) -> None:
        self.append(path=path, reason="does not exist")

    def grouped_by_path(self) -> Iterator[tuple[Path, list[str]]]:
        sorted_by_path = sorted(self.errors, key=lambda e: e.path)

        return (
            (path, [e.reason for e in errors])
            for path, errors in itertools.groupby(sorted_by_path, lambda e: e.path)
        )

    def mark_file_as_ok(self, path: Path) -> None:
        self.valid_paths.append(path)

    def count(self) -> int:
        return len(self.errors) + len(self.valid_paths)

    def okay(self) -> bool:
        return len(self.errors) == 0

    def merge(self, other: ValidationReport) -> ValidationReport:
        return ValidationReport(
            errors=self.errors + other.errors,
            valid_paths=self.valid_paths + other.valid_paths,
        )
