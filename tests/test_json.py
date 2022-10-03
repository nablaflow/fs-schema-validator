from pathlib import Path

import orjson
import pytest

from fs_schema_validator import Schema
from fs_schema_validator.report import ValidationError
from fs_schema_validator.string_expander.values import String

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_ok(schema: Schema, tmp_path: Path) -> None:
    json_path = tmp_path / "file.json"
    json_path.write_bytes(
        orjson.dumps(
            {
                "bool": True,
                "int": 10,
                "int_exclusive": 8,
                "float": 10.0,
                "float_exclusive": 8.0,
                "str": "#123456789",
                "array": [1, 2, 2, 3, 3],
                "set": [1, 2, 3],
                "tuple": [1, "2", 3.0],
                "nested": {
                    "float": 3.5,
                },
                "dict_": {
                    "foo": 1,
                    "bar": 2,
                },
                "enum": "foo",
            }
        )
    )

    assert schema.validate_(root_dir=tmp_path).errors == []


def test_root_level_fail(schema: Schema, tmp_path: Path) -> None:
    json_path = tmp_path / "file.json"
    json_path.write_bytes(orjson.dumps(1))

    assert schema.validate_(root_dir=tmp_path).errors == [
        ValidationError(
            path=Path("file.json"),
            reason="root object: value is not a valid dict",
        )
    ]


def test_binding_replacement_in_json_schema(tmp_path: Path) -> None:
    json_path = tmp_path / "file.json"
    json_path.write_bytes(orjson.dumps({"array": [1, 2, 3, 4]}))

    yaml = """
      schema:
        - type: json
          path: file.json
          spec:
            type: object
            attrs:
              array:
                type: array
                min_items: "{$count}"
                max_items: "{$count}"
                items:
                  type: int
    """

    assert (
        Schema.from_yaml(yaml, {"count": String("4")}).validate_(root_dir=tmp_path).errors
        == []
    )

    assert Schema.from_yaml(yaml, {"count": String("5")}).validate_(
        root_dir=tmp_path
    ).errors == [
        ValidationError(
            path=Path("file.json"),
            reason="`array`: ensure this value has at least 5 items",
        )
    ]


def test_expansion_escaping(tmp_path: Path) -> None:
    json_path = tmp_path / "file.json"
    json_path.write_bytes(orjson.dumps("123abc"))

    schema = Schema.from_yaml(
        """
      schema:
        - type: json
          path: file.json
          spec:
            type: string
            regex: "^[0-9a-f]{{6}}$"
    """
    )
    assert schema.validate_(root_dir=tmp_path).errors == []


def test_nullable_properties(tmp_path: Path) -> None:
    json_path = tmp_path / "file.json"
    json_path.write_bytes(orjson.dumps({}))

    schema = Schema.from_yaml(
        """
      schema:
        - type: json
          path: file.json
          spec:
            type: object
            attrs:
              foo:
                type: string
                nullable: true
    """
    )

    assert schema.validate_(root_dir=tmp_path).errors == []

    json_path.write_bytes(orjson.dumps({"foo": None}))

    assert schema.validate_(root_dir=tmp_path).errors == []


def test_nullable_items_in_array(tmp_path: Path) -> None:
    json_path = tmp_path / "file.json"
    json_path.write_bytes(orjson.dumps([1, 2, 3, None]))

    schema = Schema.from_yaml(
        """
      schema:
        - type: json
          path: file.json
          spec:
            type: array
            items:
              type: int
              nullable: true
    """
    )

    assert schema.validate_(root_dir=tmp_path).errors == []


def test_missing(schema: Schema, tmp_path: Path) -> None:
    assert schema.validate_(root_dir=tmp_path).errors == [
        ValidationError(path=Path("file.json"), reason="does not exist")
    ]


@pytest.mark.parametrize(
    "json,expected_reason",
    [
        ({}, "`bool`: field required"),
        ({}, "`int`: field required"),
        ({}, "`int_exclusive`: field required"),
        ({}, "`float`: field required"),
        ({}, "`float_exclusive`: field required"),
        ({}, "`str`: field required"),
        ({}, "`array`: field required"),
        ({}, "`set`: field required"),
        ({}, "`tuple`: field required"),
        ({}, "`nested`: field required"),
        ({"bool": 1}, "`bool`: value is not a valid boolean"),
        ({"int": "1"}, "`int`: value is not a valid integer"),
        ({"int": 3}, "`int`: ensure this value is a multiple of 2"),
        ({"int": 11}, "`int`: ensure this value is less than or equal to 10"),
        ({"int_exclusive": 11}, "`int_exclusive`: ensure this value is less than 10"),
        ({"float": "1"}, "`float`: value is not a valid float"),
        ({"float": 3.0}, "`float`: ensure this value is a multiple of 2.0"),
        ({"float": 11.0}, "`float`: ensure this value is less than or equal to 10.0"),
        (
            {"float_exclusive": 11.0},
            "`float_exclusive`: ensure this value is less than 10.0",
        ),
        ({"str": 1}, "`str`: str type expected"),
        ({"str": ""}, "`str`: ensure this value has at least 1 characters"),
        ({"str": "1"}, '`str`: string does not match regex "^#(\\d+)$"'),
        ({"str": "111111111111"}, "`str`: ensure this value has at most 10 characters"),
        ({"array": "1"}, "`array`: value is not a valid list"),
        ({"array": []}, "`array`: ensure this value has at least 1 items"),
        ({"array": ["5"]}, "`array.0`: value is not a valid integer"),
        ({"array": list(range(100))}, "`array`: ensure this value has at most 10 items"),
        ({"set": "1"}, "`set`: value is not a valid list"),
        ({"set": []}, "`set`: ensure this value has at least 1 items"),
        ({"set": ["5"]}, "`set.0`: value is not a valid integer"),
        ({"set": [1, 1, 1]}, "`set`: the list has duplicated items"),
        ({"tuple": []}, "`tuple`: wrong tuple length 0, expected 3"),
        ({"tuple": ["1", "2", 3.0]}, "`tuple.0`: value is not a valid integer"),
        ({"nested": {}}, "`nested.float`: field required"),
        ({"nested": {"float": "2"}}, "`nested.float`: value is not a valid float"),
        ({"dict_": {"foo": "bar"}}, "`dict_.foo`: value is not a valid integer"),
        ({"enum": 9.8}, "`enum`: value is not a valid integer"),
        ({"enum": 9.8}, "`enum`: str type expected"),
    ],
)
def test_fail(
    schema: Schema,
    tmp_path: Path,
    json: dict,
    expected_reason: str,
) -> None:
    json_path = tmp_path / "file.json"
    json_path.write_bytes(orjson.dumps(json))

    assert (
        ValidationError(path=Path("file.json"), reason=expected_reason)
        in schema.validate_(root_dir=tmp_path).errors
    )


@pytest.fixture
def schema() -> Schema:
    return Schema.from_yaml(
        """
      schema:
        - type: json
          path: file.json
          spec:
            type: object
            attrs:
              bool:
                type: bool
              int:
                type: int
                min: 0
                max: 10
                multiple_of: 2
              int_exclusive:
                type: int
                exclusive_min: 0
                exclusive_max: 10
              float:
                type: float
                min: 0
                max: 10
                multiple_of: 2.0
              float_exclusive:
                type: float
                exclusive_min: 0
                exclusive_max: 10
                multiple_of: 2.0
              str:
                type: str
                min_length: 1
                max_length: 10
                regex: "^#(\\\\d+)$"
              array:
                type: array
                min_items: 1
                max_items: 10
                items:
                  type: int
              set:
                type: array
                unique_items: true
                min_items: 1
                items:
                  type: int
              tuple:
                type: fixed_array
                items:
                  - type: int
                  - type: str
                  - type: float
              nested:
                type: object
                attrs:
                  float:
                    type: float
              dict_:
                type: dict
                keys:
                  type: string
                values:
                  type: int
              enum:
                type: enum
                variants:
                  - type: integer
                  - type: string
    """
    )
