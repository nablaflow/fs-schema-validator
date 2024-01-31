from pathlib import Path

from fs_schema_validator.report import ValidationReport


def _assert_path_exists(root_dir: Path, path: Path, report: ValidationReport) -> bool:
    if not (root_dir / path).exists():
        report.append_missing_file(path)
        return False

    return True
