from __future__ import annotations

from pathlib import Path
from typing import Annotated, Dict, Literal, NamedTuple, Optional, Type, Union, cast

import orjson
import pydantic
from pydantic import (
    BaseModel,
    Extra,
    Field,
    StrictBool,
    confloat,
    conint,
    conlist,
    constr,
)

from fs_schema_validator.report import ValidationReport
from fs_schema_validator.string_expander.values import Bindings
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
    ],
    Field(discriminator="type"),
]


class JsonFloat(BaseModel, extra=Extra.forbid):
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


class JsonBool(BaseModel, extra=Extra.forbid):
    type: Literal["bool", "boolean"]
    nullable: bool = False

    def gen_schema(self) -> Type:
        return _wrap_nullable(StrictBool, self.nullable)


class JsonInt(BaseModel, extra=Extra.forbid):
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


class JsonString(BaseModel, extra=Extra.forbid):
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
                regex=self.regex,
            ),
            self.nullable,
        )


class JsonArray(BaseModel, extra=Extra.forbid):
    type: Literal["array", "list"]
    items: JsonValue
    min_items: Optional[int] = None
    max_items: Optional[int] = None
    unique_items: Optional[bool] = None
    nullable: bool = False

    def gen_schema(self) -> Type:
        return _wrap_nullable(
            conlist(
                item_type=self.items.gen_schema(),
                min_items=self.min_items,
                max_items=self.max_items,
                unique_items=self.unique_items,
            ),
            self.nullable,
        )


class JsonFixedArray(BaseModel, extra=Extra.forbid):
    type: Literal["fixed_array", "tuple"]
    items: conlist(item_type=JsonValue, min_items=1)  # type: ignore[valid-type]
    nullable: bool = False

    def gen_schema(self) -> Type:
        # TODO: how to generate a Tuple[t0, t1, ..] type?
        return _wrap_nullable(
            cast(
                Type,
                NamedTuple(
                    "tuple",
                    [
                        (str(f"element_{i}"), item.gen_schema())
                        for i, item in enumerate(self.items)
                    ],
                ),
            ),
            self.nullable,
        )


class JsonObject(BaseModel, extra=Extra.forbid):
    type: Literal["object"]
    attrs: Dict[str, JsonValue]
    nullable: bool = False

    def gen_schema(self) -> Type:
        kwargs = {
            k: (v.gen_schema(), ... if not v.nullable else None)
            for k, v in self.attrs.items()
        }

        return _wrap_nullable(
            pydantic.create_model("JsonObject", **kwargs),  # type: ignore[call-overload]
            self.nullable,
        )


class JsonDict(BaseModel, extra=Extra.forbid):
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
            ],  # type: ignore[index]
            self.nullable,
        )


def _wrap_nullable(t: Type, nullable: bool) -> Type:
    if nullable:
        return cast(Type, Optional[t])
    else:
        return t


JsonArray.update_forward_refs()
JsonFixedArray.update_forward_refs()
JsonDict.update_forward_refs()
JsonObject.update_forward_refs()


class JsonSchema(BaseModel, extra=Extra.forbid):
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
            pydantic.parse_obj_as(schema, json)
        except pydantic.ValidationError as e:
            for error in e.errors():
                json_path = ".".join(
                    (str(span) for span in error["loc"] if span != "__root__")
                )

                if len(json_path) == 0:
                    reason = f"root object: {error['msg']}"
                else:
                    reason = f"`{json_path}`: {error['msg']}"

                report.append(path=self.path, reason=reason)

            return False

        return True
