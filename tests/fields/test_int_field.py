"""Integer field tests."""
from marshpy.core.errors import ErrorCode
from marshpy.fields.int_field import IntField

from tests.helpers import check_field
from tests.helpers import check_field_error


class _Test:

    fields = {
        'int': IntField(minimum=10, maximum=20),
        'hex_int': IntField(base=16)
    }


def _check_field(field: str, yml_value: str, expected_value: int) -> None:
    check_field(_Test, field, yml_value, expected_value)


def _check_field_error(
    field: str,
    yml_value: str,
    expected_error: ErrorCode
) -> None:
    check_field_error(_Test, field, yml_value, expected_error)


def test_int_field() -> None:
    """Int field should load correct values."""
    _check_field('int', '15', 15)
    _check_field('int', '0xF', 0xF)
    _check_field('int', '0o20', 0o20)
    _check_field('hex_int', 'F00D00FAFA', 0xF00D00FAFA)


def test_int_field_error_handling() -> None:
    """Int field should correctly handle errors."""
    _check_field_error('int', '[a, list]', ErrorCode.UNEXPECTED_NODE_TYPE)
    _check_field_error('int', '{a: dict}', ErrorCode.UNEXPECTED_NODE_TYPE)

    _check_field_error('int', 'bad_value', ErrorCode.VALUE_ERROR)

    # Out of bounds
    _check_field_error('int', '0', ErrorCode.VALIDATION_ERROR)
    _check_field_error('int', '100', ErrorCode.VALIDATION_ERROR)
