from __future__ import annotations

import itertools
from pathlib import Path
from typing import Iterator, List, Tuple

from pydantic import BaseModel, ConfigDict, Field


class ValidationError(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: Path
    reason: str


class ValidationReport(BaseModel):
    errors: List[ValidationError] = Field(default_factory=list)
    valid_paths: List[Path] = Field(default_factory=list)

    def append(self, path: Path, reason: str) -> None:
        self.errors.append(ValidationError(path=path, reason=reason))

    def append_missing_file(self, path: Path) -> None:
        self.append(path=path, reason="does not exist")

    def grouped_by_path(self) -> Iterator[Tuple[Path, List[str]]]:
        return map(
            lambda a: (a[0], list(map(lambda e: e.reason, a[1]))),
            itertools.groupby(
                sorted(self.errors, key=lambda e: e.path), lambda e: e.path
            ),
        )

    def mark_file_as_ok(self, path: Path) -> None:
        self.valid_paths.append(path)

    def count(self) -> int:
        return len(self.errors) + len(self.valid_paths)

    def okay(self) -> bool:
        return len(self.errors) == 0
