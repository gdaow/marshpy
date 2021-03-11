"""String field tests."""
from typing import Optional

from marshpy.core.errors import ErrorCode
from marshpy.fields.bool_field import BoolField

from tests.helpers import check_field
from tests.helpers import check_field_error


class _Test:
    """Test class for bool field tests."""

    fields = {
        'bool': BoolField()
    }

    def __init__(self) -> None:
        """Initialize _BoolObject."""
        self.bool: Optional[bool] = None


def _check_field(yaml_value: str, expected_value: bool) -> None:
    check_field(_Test, 'bool', yaml_value, expected_value)


def _check_field_error(yaml_value: str, expected_error: ErrorCode) -> None:
    check_field_error(_Test, 'bool', yaml_value, expected_error)


def test_bool_field() -> None:
    """Bool field should load correct values."""
    true_values = [
        'y', 'Y', 'yes', 'Yes', 'YES',
        'true', 'True', 'TRUE',
        'on', 'On', 'ON'
    ]

    for value in true_values:
        _check_field(value, True)

    false_values = [
        'n', 'N', 'no', 'No', 'NO',
        'false', 'False', 'FALSE'
        'off', 'Off', 'OFF'
    ]

    for value in false_values:
        _check_field(value, False)


def test_bool_field_error_handling() -> None:
    """Bool field should correctly handle errors."""
    _check_field_error('[a, list]', ErrorCode.UNEXPECTED_NODE_TYPE)
    _check_field_error('{a: dict}', ErrorCode.UNEXPECTED_NODE_TYPE)

    _check_field_error('bad_value', ErrorCode.VALUE_ERROR)
