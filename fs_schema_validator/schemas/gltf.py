from enum import Enum, unique
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pygltflib import GLTF2

from fs_schema_validator.report import ValidationReport
from fs_schema_validator.string_expander.values import Bindings, String
from fs_schema_validator.utils import _assert_path_exists


@unique
class GltfFormat(Enum):
    GLTF = "gltf"
    GLB = "glb"


class GltfSchema(BaseModel):
    type: Literal["gltf"]
    format: GltfFormat
    path: Path

    def inner_bindings(self) -> Bindings:
        return {
            "format": String(self.format.value),
        }

    def validate_(self, root_dir: Path, report: ValidationReport) -> bool:
        if not _assert_path_exists(root_dir, self.path, report):
            return False

        try:
            if self.format == GltfFormat.GLTF:
                gltf = GLTF2.load_json(root_dir / self.path)
            elif self.format == GltfFormat.GLB:
                gltf = GLTF2.load_binary(root_dir / self.path)
        except Exception as e:
            report.append(
                path=self.path, reason=f"failed to deserialize: ({type(e)}) {e}"
            )
            return False

        if len(gltf.nodes) == 0:
            report.append(path=self.path, reason="file does not contain nodes")
            return False

        return True
