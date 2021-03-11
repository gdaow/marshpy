"""first-of tag handler tests."""
from typing import Any
from typing import Optional

from marshpy.core.constants import UNDEFINED
from marshpy.core.errors import ErrorCode
from marshpy.fields.string_field import StringField
from marshpy.tag_handlers.first_of_handler import FirstOfHandler

from tests.helpers import check_load


def _check_first_of_tag(
    yaml: str,
    expected_value: Any = None,
    expected_error: Optional[ErrorCode] = None
) -> None:
    if expected_error is not None:
        expected_value = UNDEFINED

    result = check_load(
        yaml,
        field=StringField(),
        tag_handlers=[
            FirstOfHandler()
        ],
        expected_error=expected_error
    )

    assert result == expected_value


def test_first_of_tag_handler() -> None:
    """First of tag should load first non-failure value in a list."""
    _check_first_of_tag(
        '!first-of [!fail value_1, !fail value_2, value_3]',
        'value_3'
    )

    _check_first_of_tag(
        '!first-of [!fail value_1, !fail value_2, !fail value_3]',
        UNDEFINED
    )


def test_first_of_tag_handler_error_handling() -> None:
    """First of tag should correctly handle errors."""
    _check_first_of_tag(
        '!first-of scalar_value',
        expected_error=ErrorCode.UNEXPECTED_NODE_TYPE
    )

    _check_first_of_tag(
        '!first-of {}',
        expected_error=ErrorCode.UNEXPECTED_NODE_TYPE
    )
