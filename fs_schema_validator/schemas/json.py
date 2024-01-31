from __future__ import annotations

from pathlib import Path
from typing import Annotated, Dict, Literal, Optional, Tuple, Type, Union, cast

import orjson
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
    Field(discriminator="type"),
]


class JsonFloat(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["float"]
    min: Optional[float] = None
    exclusive_min: Optional[float] = None
    max: Optional[float] = None
    exclusive_max: Optional[float] = None
    multiple_of: Optional[float] = None
    nullable: bool = False

    def gen_schema(self) -> Type:
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
    type: Literal["bool", "boolean"]
    nullable: bool = False

    def gen_schema(self) -> Type:
        return _wrap_nullable(StrictBool, self.nullable)


class JsonInt(BaseModel, extra="forbid"):
    type: Literal["int", "integer"]
    min: Optional[int] = None
    exclusive_min: Optional[int] = None
    max: Optional[int] = None
    exclusive_max: Optional[int] = None
    multiple_of: Optional[int] = None
    nullable: bool = False

    def gen_schema(self) -> Type:
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
    type: Literal["str", "string"]
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    regex: Optional[str] = None
    nullable: bool = False

    def gen_schema(self) -> Type:
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
    type: Literal["array", "list"]
    items: JsonValue
    min_items: Optional[int] = None
    max_items: Optional[int] = None
    nullable: bool = False

    def gen_schema(self) -> Type:
        return _wrap_nullable(
            conlist(
                item_type=self.items.gen_schema(),
                min_length=self.min_items,
                max_length=self.max_items,
            ),
            self.nullable,
        )


class JsonFixedArray(BaseModel, extra="forbid"):
    type: Literal["fixed_array", "tuple"]
    items: conlist(item_type=JsonValue, min_length=1)  # type: ignore[valid-type]
    nullable: bool = False

    def gen_schema(self) -> Type:
        return _wrap_nullable(
            cast(Type, Tuple[tuple((v.gen_schema() for v in self.items))]),
            self.nullable,
        )


class JsonObject(BaseModel, extra="forbid"):
    type: Literal["object"]
    attrs: Dict[str, JsonValue]
    nullable: bool = False

    def gen_schema(self) -> Type:
        kwargs = {
            k: (v.gen_schema(), ... if not v.nullable else None) for k, v in self.attrs.items()
        }

        return _wrap_nullable(
            pydantic.create_model("JsonObject", **kwargs),  # type: ignore[call-overload]
            self.nullable,
        )


class JsonDict(BaseModel, extra="forbid"):
    type: Literal["dict"]
    keys: JsonValue
    values: JsonValue
    nullable: bool = False
    # TODO: allow items count constraints
    #  min_items: Optional[int] = None
    #  max_items: Optional[int] = None

    def gen_schema(self) -> Type:
        return _wrap_nullable(
            Dict[  # type: ignore[misc]
                self.keys.gen_schema(),
                self.values.gen_schema(),
            ],
            self.nullable,
        )


class JsonEnum(BaseModel, extra="forbid"):
    type: Literal["enum"]
    variants: conlist(item_type=JsonValue, min_length=1)  # type: ignore[valid-type]
    nullable: bool = False

    def gen_schema(self) -> Type:
        return _wrap_nullable(
            cast(Type, Union[tuple((v.gen_schema() for v in self.variants))]),
            self.nullable,
        )


class JsonLiteral(BaseModel, extra="forbid"):
    type: Literal["literal"]
    value: Union[constr(strict=True), conint(strict=True), confloat(strict=True)]  # type: ignore[valid-type]
    nullable: bool = False

    def gen_schema(self) -> Type:
        return _wrap_nullable(cast(Type, Literal[self.value]), self.nullable)


def _wrap_nullable(t: Type, nullable: bool) -> Type:
    if nullable:
        return cast(Type, Optional[t])

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

        with (root_dir / self.path).open() as f:
            try:
                json = orjson.loads(f.read())
            except orjson.JSONDecodeError as e:
                report.append(path=self.path, reason=f"invalid json file: {e}")
                return False

        schema = self.spec.gen_schema()

        try:
            TypeAdapter(schema).validate_python(json)
        except pydantic.ValidationError as e:
            for error in e.errors():
                json_path = ".".join(
                    (
                        str(span)
                        for span in error["loc"]
                        if span != "__root__" and not str(span).startswith("literal[")
                    )
                )

                if len(json_path) == 0:
                    reason = f"root object: {error['msg']}"
                else:
                    reason = f"`{json_path}`: {error['msg']}"

                report.append(path=self.path, reason=reason)

            return False

        return True
