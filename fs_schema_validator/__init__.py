from __future__ import annotations

import typing
from pathlib import Path
from typing import Annotated, Dict, Iterator, List, Set, Tuple, Union

import pydantic
import yaml
from pydantic import BaseModel, Field

if typing.TYPE_CHECKING:
    from _typeshed import SupportsRead

import fs_schema_validator.string_expander as string_expander
from fs_schema_validator.report import ValidationReport
from fs_schema_validator.schemas.gltf import GltfSchema
from fs_schema_validator.schemas.image import ImageSchema
from fs_schema_validator.schemas.json import JsonSchema
from fs_schema_validator.string_expander.values import Bindings, Enum, Range

Validator = Annotated[
    Union[
        JsonSchema,
        ImageSchema,
        GltfSchema,
    ],
    Field(discriminator="type"),
]


class Schema(BaseModel):
    validators: List[Validator] = Field(alias="schema")
    bindings: Dict[str, Union[Tuple[int, int], Set[str]]] = Field(default_factory=dict)

    @staticmethod
    def from_yaml(
        f: Union[str, bytes, "SupportsRead[str]", "SupportsRead[bytes]"]
    ) -> Schema:
        return Schema(**yaml.safe_load(f))

    def validate_(
        self, root_dir: Path, extra_bindings: Bindings = {}
    ) -> ValidationReport:
        bindings = {**self._convert_bindings(), **extra_bindings}

        report = ValidationReport()

        for validator in self.validators:
            for expanded_validator in _expand(validator, bindings):
                if expanded_validator.validate_(root_dir, report):
                    report.mark_file_as_ok(expanded_validator.path)

        return report

    def _convert_bindings(self) -> Bindings:
        b: Bindings = {}

        for k, v in self.bindings.items():
            if isinstance(v, set):
                b[k] = Enum(v)
            elif isinstance(v, tuple):
                b[k] = Range(v[0], v[1])

        return b


def _expand(validator: Validator, bindings: Bindings) -> Iterator[Validator]:
    expanded_paths = string_expander.expand(str(validator.path), bindings)

    for path in map(Path, expanded_paths):
        expanded_validator = validator.copy()
        expanded_validator.path = path

        yield expanded_validator
