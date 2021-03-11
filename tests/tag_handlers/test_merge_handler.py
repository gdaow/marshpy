"""Merge tag handler tests."""
from typing import Any
from typing import Optional

from marshpy.core.constants import UNDEFINED
from marshpy.core.errors import ErrorCode
from marshpy.fields.base_field import BaseField
from marshpy.fields.dict_field import DictField
from marshpy.fields.list_field import ListField
from marshpy.fields.string_field import StringField
from marshpy.tag_handlers.merge_handler import MergeHandler

from tests.helpers import check_load


def _check_merge_tag(
    field: BaseField,
    yaml: str,
    expected_value: Any = None,
    expected_error: Optional[ErrorCode] = None
) -> None:
    if expected_error is not None:
        expected_value = UNDEFINED

    result = check_load(
        yaml,
        field=field,
        tag_handlers=[
            MergeHandler()
        ],
        expected_error=expected_error
    )

    assert result == expected_value


def test_merge_tag_handler() -> None:
    """Merge tag handler should correctly merge dictionnaries & lists."""
    # Merging list should work
    _check_merge_tag(
        ListField(StringField()),
        '!merge [[value_1, value_2], [value_3]]',
        ['value_1', 'value_2', 'value_3']
    )

    # Merging dicts should work
    _check_merge_tag(
        DictField(StringField()),
        '!merge [{a: a_value, b: b_value}, {b: overwrite_b}]',
        {'a': 'a_value', 'b': 'overwrite_b'}
    )

    # An undefined value in the sequence should be ignored
    _check_merge_tag(
        ListField(StringField()),
        '!merge [[value_1, value_2], !fail [value_3]]',
        ['value_1', 'value_2']
    )

    # An empty sequence should return UNDEFINED
    _check_merge_tag(
        ListField(StringField()),
        '!merge []',
        UNDEFINED
    )


def test_merge_tag_handler_error_handling() -> None:
    """Merge tag should correctly handle errors."""
    _check_merge_tag(
        ListField(StringField()),
        '!merge scalar_value',
        expected_error=ErrorCode.UNEXPECTED_NODE_TYPE
    )

    _check_merge_tag(
        ListField(StringField()),
        '!merge {}',
        expected_error=ErrorCode.UNEXPECTED_NODE_TYPE
    )

    _check_merge_tag(
        StringField(),
        '!merge [scalar_value]',
        expected_error=ErrorCode.VALUE_ERROR
    )
