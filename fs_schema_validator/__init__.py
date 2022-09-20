from __future__ import annotations

import typing
from io import StringIO
from itertools import chain, product
from pathlib import Path
from typing import Annotated, Any, Dict, Iterator, List, Set, Tuple, TypedDict, Union

import pydantic
import yaml
from pydantic import BaseModel, Field, parse_obj_as

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


UntypedBindings = Annotated[
    Dict[str, Union[Tuple[int, int], Set[str]]], Field(default_factory=dict)
]


class Schema(BaseModel):
    validators: List[Validator]

    @staticmethod
    def from_yaml(
        f: Union[str, bytes, "SupportsRead[str]", "SupportsRead[bytes]"],
        extra_bindings: Bindings = {},
    ) -> Schema:
        class UntypedSchema(BaseModel):
            validators: List[Dict[str, Any]] = Field(alias="schema")
            bindings: UntypedBindings

        untyped_schema = UntypedSchema(**yaml.safe_load(f))

        bindings = {**_type_bindings(untyped_schema.bindings), **extra_bindings}

        expanded_untyped_validators = list(
            chain.from_iterable(
                (
                    _expand_untyped_validator(untyped_validator, bindings)
                    for untyped_validator in untyped_schema.validators
                )
            )
        )

        return Schema(validators=expanded_untyped_validators)

    def validate_(self, root_dir: Path) -> ValidationReport:
        report = ValidationReport()

        for validator in self.validators:
            validator_with_expanded_path = _expand_path(validator)
            if validator_with_expanded_path.validate_(root_dir, report):
                report.mark_file_as_ok(validator_with_expanded_path.path)

        return report


def _expand_path(validator: Validator) -> Validator:
    path = list(string_expander.expand(str(validator.path), validator.inner_bindings()))
    assert (
        len(path) == 1
    ), "cannot expand to more than one variant when dealing with paths and a validator's inner bindings"

    validator = validator.copy()
    validator.path = Path(path[0])

    return validator


def _type_bindings(untyped_bindings: UntypedBindings) -> Bindings:
    b: Bindings = {}

    for k, v in untyped_bindings.items():
        if isinstance(v, set):
            b[k] = Enum(v)
        elif isinstance(v, tuple):
            b[k] = Range(v[0], v[1])

    return b


def _expand_untyped_validator(
    validator: Dict[str, Any], bindings: Bindings
) -> Iterator[dict]:
    expanded_validator: Dict[str, Iterator[str]] = {
        key: _expand_any(value, bindings) for key, value in validator.items()
    }

    return map(
        dict,
        product(
            *[[(key, value) for value in it] for key, it in expanded_validator.items()]
        ),
    )


def _expand_any(value: Any, bindings: Bindings) -> Iterator[Any]:
    if isinstance(value, str):
        return string_expander.expand(value, bindings, leave_unbound_vars_in=True)
    else:
        # TODO: this is a hack, figure out a way to easily evaluate a potential binding in a nested object
        yaml_ = yaml.safe_dump(value)
        yamls = list(_expand_any(yaml_, bindings))
        assert (
            len(yamls) == 1
        ), "cannot expand to more than one variant when dealing with nested object"
        return iter([yaml.safe_load(StringIO(yamls[0]))])
