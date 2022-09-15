from __future__ import annotations

import typing
from pathlib import Path
from typing import Annotated, List, Union

import pydantic
import yaml
from pydantic import BaseModel, Field

if typing.TYPE_CHECKING:
    from _typeshed import SupportsRead

from fs_schema_validator.report import ValidationReport
from fs_schema_validator.schemas.gltf import GltfSchema
from fs_schema_validator.schemas.image import ImageSchema
from fs_schema_validator.schemas.json import JsonSchema

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

    @staticmethod
    def from_yaml(
        f: Union[str, bytes, "SupportsRead[str]", "SupportsRead[bytes]"]
    ) -> Schema:
        return Schema(**yaml.safe_load(f))

    def validate_(self, root_dir: Path) -> ValidationReport:
        report = ValidationReport()

        for validator in self.validators:
            count = len(report.errors)

            validator.validate_(root_dir, report)

            if count == len(report.errors):
                report.mark_file_as_ok(validator.path)

        return report
