"""Path field tests."""
from pathlib import Path

from marshpy.core.errors import ErrorCode
from marshpy.fields.path_field import PathField
from tests.helpers import check_field, check_field_error, check_load


class _Test:

    fields = {"path": PathField(), "path_not_checked": PathField(must_exist=False)}


def _check_field(yaml_value: str, expected_value: Path) -> None:
    check_field(_Test, "path", yaml_value, expected_value)


def _check_field_error(yaml_value: str, expected_error: ErrorCode) -> None:
    check_field_error(_Test, "path", yaml_value, expected_error)


def test_path_field(datadir: Path) -> None:
    """Path field should load correct values."""
    # Absolute path
    file_path = datadir / "some_file.txt"
    _check_field(str(file_path), file_path)

    # Relative path
    file_path = datadir / "file.yaml"
    with open(file_path, "r", encoding="utf-8") as yaml_file:
        result = check_load(yaml_file, _Test, location=str(file_path))
        assert result.path == datadir / "some_file.txt"

    result = check_load("path_not_checked: doesnt_exists.txt", _Test)
    assert result.path_not_checked == Path("doesnt_exists.txt")


def test_path_field_error_handling() -> None:
    """Path field should correctly handle errors."""
    _check_field_error("[a, list]", ErrorCode.UNEXPECTED_NODE_TYPE)
    _check_field_error("{a: dict}", ErrorCode.UNEXPECTED_NODE_TYPE)
    _check_field_error("doesnt_exists.txt", ErrorCode.VALIDATION_ERROR)
