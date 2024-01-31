from pathlib import Path

import orjson
import pytest

from fs_schema_validator import Schema
from fs_schema_validator.evaluator.values import String
from fs_schema_validator.report import ValidationError

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
                "tuple": [1, "2", 3.0],
                "nested": {
                    "float": 3.5,
                },
                "dict_": {
                    "foo": 1,
                    "bar": 2,
                },
                "enum": "foo",
                "literal_str": "foo",
                "literal_int": 5,
                "literal_float": 5.5,
                "enum2": "foo",
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
            reason="root object: Input should be a valid dictionary or instance of JsonObject",
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

    assert Schema.from_yaml(yaml, {"count": String("4")}).validate_(root_dir=tmp_path).errors == []

    assert Schema.from_yaml(yaml, {"count": String("5")}).validate_(root_dir=tmp_path).errors == [
        ValidationError(
            path=Path("file.json"),
            reason="`array`: List should have at least 5 items after validation, not 4",
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
        ({}, "`bool`: Field required"),
        ({}, "`int`: Field required"),
        ({}, "`int_exclusive`: Field required"),
        ({}, "`float`: Field required"),
        ({}, "`float_exclusive`: Field required"),
        ({}, "`str`: Field required"),
        ({}, "`array`: Field required"),
        ({}, "`tuple`: Field required"),
        ({}, "`nested`: Field required"),
        ({"bool": 1}, "`bool`: Input should be a valid boolean"),
        ({"int": "1"}, "`int`: Input should be a valid integer"),
        ({"int": 3}, "`int`: Input should be a multiple of 2"),
        ({"int": 12}, "`int`: Input should be less than or equal to 10"),
        ({"int_exclusive": 11}, "`int_exclusive`: Input should be less than 10"),
        ({"float": "1"}, "`float`: Input should be a valid number"),
        ({"float": 3.0}, "`float`: Input should be a multiple of 2"),
        ({"float": 12.0}, "`float`: Input should be less than or equal to 10"),
        (
            {"float_exclusive": 11.0},
            "`float_exclusive`: Input should be less than 10",
        ),
        ({"str": 1}, "`str`: Input should be a valid string"),
        ({"str": ""}, "`str`: String should have at least 1 character"),
        ({"str": "1"}, "`str`: String should match pattern '^#(\\d+)$'"),
        ({"str": "111111111111"}, "`str`: String should have at most 10 characters"),
        ({"array": "1"}, "`array`: Input should be a valid list"),
        (
            {"array": []},
            "`array`: List should have at least 1 item after validation, not 0",
        ),
        ({"array": ["5"]}, "`array.0`: Input should be a valid integer"),
        (
            {"array": list(range(100))},
            "`array`: List should have at most 10 items after validation, not 100",
        ),
        ({"tuple": []}, "`tuple.0`: Field required"),
        ({"tuple": ["1", "2", 3.0]}, "`tuple.0`: Input should be a valid integer"),
        ({"nested": {}}, "`nested.float`: Field required"),
        ({"nested": {"float": "2"}}, "`nested.float`: Input should be a valid number"),
        ({"dict_": {"foo": "bar"}}, "`dict_.foo`: Input should be a valid integer"),
        ({"enum": 9.8}, "`enum.int`: Input should be a valid integer"),
        ({"enum": 9.8}, "`enum.str`: Input should be a valid string"),
        ({"literal_str": 9.8}, "`literal_str`: Input should be 'foo'"),
        ({"literal_int": 9.8}, "`literal_int`: Input should be 5"),
        ({"literal_float": 2}, "`literal_float`: Input should be 5.5"),
        ({"enum2": "baz"}, "`enum2`: Input should be 'foo'"),
        ({"enum2": "baz"}, "`enum2`: Input should be 'bar'"),
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
                  - type: int
                  - type: str
              literal_str:
                type: literal
                value: "foo"
              literal_int:
                type: literal
                value: 5
              literal_float:
                type: literal
                value: 5.5
              enum2:
                type: enum
                variants:
                  - type: literal
                    value: "foo"
                  - type: literal
                    value: "bar"
    """
    )
