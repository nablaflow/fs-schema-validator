from __future__ import annotations

import typing
from collections.abc import Iterator
from concurrent.futures import ProcessPoolExecutor
from io import StringIO
from itertools import chain, product
from pathlib import Path
from typing import Annotated, Any

import yaml
from pydantic import BaseModel, Field

if typing.TYPE_CHECKING:
    from _typeshed import SupportsRead

from fs_schema_validator import evaluator
from fs_schema_validator.evaluator.values import Bindings, Enum, Range, String
from fs_schema_validator.report import ValidationReport
from fs_schema_validator.schemas.file import FileSchema
from fs_schema_validator.schemas.gltf import GltfSchema
from fs_schema_validator.schemas.image import ImageSchema
from fs_schema_validator.schemas.json import JsonSchema
from fs_schema_validator.schemas.zip import ZipSchema

Validator = Annotated[
    JsonSchema | ImageSchema | GltfSchema | FileSchema | ZipSchema,
    Field(discriminator="type"),
]


UntypedBindings = Annotated[
    dict[str, tuple[int, int] | set[str] | str], Field(default_factory=dict)
]

UntypedValidator = dict[str, Any]


class UntypedSchema(BaseModel):
    validators: list[UntypedValidator] = Field(alias="schema")
    bindings: UntypedBindings


class Schema(BaseModel):
    validators: list[Validator]

    @staticmethod
    def from_yaml(
        f: str | bytes | SupportsRead[str] | SupportsRead[bytes],
        extra_bindings: Bindings | None = None,
    ) -> Schema:
        if extra_bindings is None:
            extra_bindings = {}

        untyped_schema = UntypedSchema(**yaml.safe_load(f))

        bindings = {**_type_bindings(untyped_schema.bindings), **extra_bindings}

        filtered_untyped_validators = list(
            _filter_validators_via_evaluation(untyped_schema.validators, bindings)
        )

        expanded_untyped_validators = list(
            chain.from_iterable(
                _expand_untyped_validator(untyped_validator, bindings)
                for untyped_validator in filtered_untyped_validators
            )
        )

        return Schema(validators=expanded_untyped_validators)

    def validate_(self, root_dir: Path) -> ValidationReport:
        report = ValidationReport()

        with ProcessPoolExecutor() as exec:
            try:
                futs = [
                    exec.submit(_job, validator=validator, root_dir=root_dir)
                    for validator in self.validators
                ]

                for fut in futs:
                    report = report.merge(fut.result(timeout=30))
            finally:
                exec.shutdown(wait=False, cancel_futures=True)

        return report


def _job(root_dir: Path, validator: Validator) -> ValidationReport:
    report = ValidationReport()

    validator_with_expanded_path = _expand_path(validator)

    if validator_with_expanded_path.validate_(root_dir, report):
        report.mark_file_as_ok(validator_with_expanded_path.path)

    return report


def _expand_path(validator: Validator) -> Validator:
    path = list(evaluator.expand(str(validator.path), validator.inner_bindings()))
    assert len(path) == 1, (
        "cannot expand to more than one variant when dealing with paths and a validator's inner bindings"
    )

    validator = validator.model_copy()
    validator.path = Path(path[0])

    return validator


def _type_bindings(untyped_bindings: UntypedBindings) -> Bindings:
    b: Bindings = {}

    for k, v in untyped_bindings.items():
        if isinstance(v, set):
            b[k] = Enum(v)
        elif isinstance(v, tuple):
            b[k] = Range(v[0], v[1])
        elif isinstance(v, str):
            b[k] = String(v)

    return b


def _expand_untyped_validator(
    validator: dict[str, Any], bindings: Bindings
) -> Iterator[dict[str, Any]]:
    expanded_validator: dict[str, Iterator[str]] = {
        key: _expand_any(value, bindings) for key, value in validator.items()
    }

    return map(
        dict,
        product(*[[(key, value) for value in it] for key, it in expanded_validator.items()]),
    )


def _expand_any(value: Any, bindings: Bindings) -> Iterator[Any]:
    if isinstance(value, str):
        return evaluator.expand(value, bindings, leave_unbound_vars_in=True)

    # TODO: this is a hack, figure out a way to easily evaluate a potential binding in a nested object
    yaml_ = yaml.safe_dump(value)
    yamls = list(_expand_any(yaml_, bindings))
    assert len(yamls) == 1, "cannot expand to more than one variant when dealing with nested object"
    return iter([yaml.safe_load(StringIO(yamls[0]))])


def _filter_validators_via_evaluation(
    validators: list[UntypedValidator], bindings: Bindings
) -> Iterator[UntypedValidator]:
    for v in validators:
        if "if" in v:
            if_ = v["if"]
            del v["if"]

            if evaluator.evaluate(if_, bindings) is True:
                yield v
        else:
            yield v
