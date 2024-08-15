from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal, Union, cast

import pydantic
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    TypeAdapter,
    confloat,
    conint,
    conlist,
    constr,
)

from fs_schema_validator.evaluator.values import Bindings
from fs_schema_validator.report import ValidationReport
from fs_schema_validator.utils import _assert_path_exists

JsonValue = Annotated[
    Union[
        "JsonArray",
        "JsonBool",
        "JsonFixedArray",
        "JsonFloat",
        "JsonInt",
        "JsonObject",
        "JsonDict",
        "JsonString",
        "JsonEnum",
        "JsonLiteral",
    ],
    Field(discriminator="t"),
]


class JsonFloat(BaseModel):
    model_config = ConfigDict(extra="forbid")

    t: Literal["float"] = Field(alias="type")
    min: float | None = None
    exclusive_min: float | None = None
    max: float | None = None
    exclusive_max: float | None = None
    multiple_of: float | None = None
    nullable: bool = False

    def gen_schema(self) -> type:
        return _wrap_nullable(
            confloat(
                strict=True,
                ge=self.min,
                le=self.max,
                gt=self.exclusive_min,
                lt=self.exclusive_max,
                multiple_of=self.multiple_of,
            ),
            self.nullable,
        )


class JsonBool(BaseModel, extra="forbid"):
    t: Literal["bool", "boolean"] = Field(alias="type")
    nullable: bool = False

    def gen_schema(self) -> type:
        return _wrap_nullable(StrictBool, self.nullable)


class JsonInt(BaseModel, extra="forbid"):
    t: Literal["int", "integer"] = Field(alias="type")
    min: int | None = None
    exclusive_min: int | None = None
    max: int | None = None
    exclusive_max: int | None = None
    multiple_of: int | None = None
    nullable: bool = False

    def gen_schema(self) -> type:
        return _wrap_nullable(
            conint(
                strict=True,
                ge=self.min,
                le=self.max,
                gt=self.exclusive_min,
                lt=self.exclusive_max,
                multiple_of=self.multiple_of,
            ),
            self.nullable,
        )


class JsonString(BaseModel, extra="forbid"):
    t: Literal["str", "string"] = Field(alias="type")
    min_length: int | None = None
    max_length: int | None = None
    regex: str | None = None
    nullable: bool = False

    def gen_schema(self) -> type:
        return _wrap_nullable(
            constr(
                strict=True,
                min_length=self.min_length,
                max_length=self.max_length,
                pattern=self.regex,
            ),
            self.nullable,
        )


class JsonArray(BaseModel, extra="forbid"):
    t: Literal["array", "list"] = Field(alias="type")
    items: JsonValue
    min_items: int | None = None
    max_items: int | None = None
    nullable: bool = False

    def gen_schema(self) -> type:
        return _wrap_nullable(
            conlist(
                item_type=self.items.gen_schema(),
                min_length=self.min_items,
                max_length=self.max_items,
            ),
            self.nullable,
        )


class JsonFixedArray(BaseModel, extra="forbid"):
    t: Literal["fixed_array", "tuple"] = Field(alias="type")
    items: conlist(item_type=JsonValue, min_length=1)  # type: ignore[valid-type]
    nullable: bool = False

    def gen_schema(self) -> type:
        return _wrap_nullable(
            cast(type, tuple[tuple(v.gen_schema() for v in self.items)]),  # type: ignore[misc]
            self.nullable,
        )


class JsonObject(BaseModel, extra="forbid"):
    t: Literal["object"] = Field(alias="type")
    attrs: dict[str, JsonValue]
    nullable: bool = False

    def gen_schema(self) -> type:
        kwargs = {
            k: (v.gen_schema(), ... if not v.nullable else None) for k, v in self.attrs.items()
        }

        return _wrap_nullable(
            pydantic.create_model("JsonObject", **kwargs),  # type: ignore[call-overload]
            self.nullable,
        )


class JsonDict(BaseModel, extra="forbid"):
    t: Literal["dict"] = Field(alias="type")
    keys: JsonValue
    values: JsonValue
    nullable: bool = False
    # TODO: allow items count constraints

    def gen_schema(self) -> type:
        return _wrap_nullable(
            dict[  # type: ignore[misc, arg-type]
                self.keys.gen_schema(),
                self.values.gen_schema(),
            ],
            self.nullable,
        )


class JsonEnum(BaseModel, extra="forbid"):
    t: Literal["enum"] = Field(alias="type")
    variants: conlist(item_type=JsonValue, min_length=1)  # type: ignore[valid-type]
    nullable: bool = False

    def gen_schema(self) -> type:
        return _wrap_nullable(
            cast(type, Union[tuple(v.gen_schema() for v in self.variants)]),  # noqa: UP007
            self.nullable,
        )


class JsonLiteral(BaseModel, extra="forbid"):
    t: Literal["literal"] = Field(alias="type")
    value: constr(strict=True) | conint(strict=True) | confloat(strict=True)  # type: ignore[valid-type]
    nullable: bool = False

    def gen_schema(self) -> type:
        return _wrap_nullable(cast(type, Literal[self.value]), self.nullable)


def _wrap_nullable(t: type, nullable: bool) -> type:
    if nullable:
        return cast(type, t | None)

    return t


JsonArray.model_rebuild()
JsonFixedArray.model_rebuild()
JsonDict.model_rebuild()
JsonObject.model_rebuild()
JsonEnum.model_rebuild()


class JsonSchema(BaseModel, extra="forbid"):
    type: Literal["json"]
    path: Path
    spec: JsonValue

    def inner_bindings(self) -> Bindings:
        return {}

    def validate_(self, root_dir: Path, report: ValidationReport) -> bool:
        if not _assert_path_exists(root_dir, self.path, report):
            return False

        schema = TypeAdapter[type](self.spec.gen_schema())

        try:
            schema.validate_json((root_dir / self.path).read_bytes())
        except pydantic.ValidationError as e:
            for error in e.errors():
                json_path = ".".join(
                    str(span)
                    for span in error["loc"]
                    if span != "__root__" and not str(span).startswith("literal[")
                )

                if len(json_path) == 0:
                    reason = f"root object: {error['msg']}"
                else:
                    reason = f"`{json_path}`: {error['msg']}"

                report.append(path=self.path, reason=reason)

            return False

        return True
