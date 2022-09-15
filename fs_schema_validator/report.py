from __future__ import annotations

import itertools
from pathlib import Path
from typing import Iterator, List, Tuple

from pydantic import BaseModel


class ValidationError(BaseModel):
    path: Path
    reason: str


class ValidationReport(BaseModel):
    errors: List[ValidationError] = []
    valid_paths: List[Path] = []

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
