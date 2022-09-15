from pathlib import Path

import orjson
import pytest

from fs_schema_validator import Schema
from fs_schema_validator.report import ValidationError

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_empty_schema_ok(tmp_path: Path) -> None:
    schema = Schema.from_yaml(
        """
      schema: []
    """
    )
    assert schema.validate_(root_dir=tmp_path).errors == []


def test_simple_schema_fail(simple_schema: Schema, tmp_path: Path) -> None:
    assert simple_schema.validate_(root_dir=tmp_path).errors == [
        ValidationError(path=Path("foo.png"), reason="does not exist"),
        ValidationError(path=Path("bar.json"), reason="does not exist"),
    ]


def test_simple_schema_ok(simple_schema: Schema, tmp_path: Path) -> None:
    (tmp_path / "foo.png").symlink_to(FIXTURES_DIR / "image.png")

    json_path = tmp_path / "bar.json"
    json_path.write_bytes(orjson.dumps({"foo": 1, "bar": "bar", "baz": 3.0}))

    assert simple_schema.validate_(root_dir=tmp_path).errors == []


def test_complex_json_schema_ok(complex_json_schema: Schema, tmp_path: Path) -> None:
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
            }
        )
    )

    assert complex_json_schema.validate_(root_dir=tmp_path).errors == []


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
        ({"tuple": []}, "`tuple.element_0`: field required"),
        ({"tuple": []}, "`tuple.element_1`: field required"),
        ({"tuple": []}, "`tuple.element_2`: field required"),
        ({"tuple": ["1", "2", 3.0]}, "`tuple.element_0`: value is not a valid integer"),
        ({"nested": {}}, "`nested.float`: field required"),
        ({"nested": {"float": "2"}}, "`nested.float`: value is not a valid float"),
    ],
)
def test_complex_json_schema_fail(
    complex_json_schema: Schema,
    tmp_path: Path,
    json: dict,
    expected_reason: str,
) -> None:
    json_path = tmp_path / "file.json"
    json_path.write_bytes(orjson.dumps(json))

    assert (
        ValidationError(path=Path("file.json"), reason=expected_reason)
        in complex_json_schema.validate_(root_dir=tmp_path).errors
    )


@pytest.fixture
def simple_schema() -> Schema:
    return Schema.from_yaml(
        """
      schema:
        - type: image
          format: png
          path: foo.png
        - type: json
          path: bar.json
          spec:
            type: object
            attrs:
              foo:
                type: int
              bar:
                type: str
              baz:
                type: float
    """
    )


@pytest.fixture
def complex_json_schema() -> Schema:
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
                minimum: 0
                maximum: 10
                multiple_of: 2
              int_exclusive:
                type: int
                exclusive_minimum: 0
                exclusive_maximum: 10
              float:
                type: float
                minimum: 0
                maximum: 10
                multiple_of: 2.0
              float_exclusive:
                type: float
                exclusive_minimum: 0
                exclusive_maximum: 10
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
                inner:
                  type: int
              set:
                type: array
                unique_items: true
                min_items: 1
                inner:
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
    """
    )
