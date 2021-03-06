"""String field tests."""
from marshpy.core.errors import ErrorCode
from marshpy.fields.string_field import StringField
from tests.helpers import check_field, check_field_error


class _Test:

    fields = {"string": StringField(pattern="^matching$")}


def _check_field(yml_value: str, expected_value: str) -> None:
    check_field(_Test, "string", yml_value, expected_value)


def _check_field_error(yml_value: str, expected_error: ErrorCode) -> None:
    check_field_error(_Test, "string", yml_value, expected_error)


def test_string_field() -> None:
    """String field should load correct values."""
    _check_field("matching", "matching")


def test_string_field_error_handling() -> None:
    """String field should correctly handle errors."""
    _check_field_error("[a, list]", ErrorCode.UNEXPECTED_NODE_TYPE)
    _check_field_error("{a: dict}", ErrorCode.UNEXPECTED_NODE_TYPE)

    _check_field_error("not_matching", ErrorCode.VALIDATION_ERROR)
