from pathlib import Path

from fs_schema_validator.report import ValidationError, ValidationReport


def _assert_path_exists(root_dir: Path, path: Path, report: ValidationReport) -> bool:
    if not (root_dir / path).exists():
        report.errors.append(ValidationError.missing_path(path))
        return False

    return True