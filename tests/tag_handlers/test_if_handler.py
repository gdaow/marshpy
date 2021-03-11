"""If tag handler tests."""
from marshpy.core.constants import UNDEFINED
from marshpy.fields.dict_field import DictField
from marshpy.fields.list_field import ListField
from marshpy.fields.string_field import StringField
from marshpy.tag_handlers.if_handler import IfHandler

from tests.helpers import check_load


def test_if_tag_handler() -> None:
    """If tag should load value only if tag is defined."""
    result = check_load(
        '!if(FLAG) test_value',
        field=StringField(),
        tag_handlers=[IfHandler()],
        config=[
            IfHandler.Config({'FLAG'})
        ]
    )
    assert result == 'test_value'

    result = check_load(
        '!if(UNDEFINED) test_value',
        field=StringField(),
        tag_handlers=[IfHandler()],
        config=[
            IfHandler.Config({'FLAG'})
        ]
    )
    assert result == UNDEFINED

    result = check_load(
        '!if(FLAG) {key: value}',
        field=DictField(StringField()),
        tag_handlers=[IfHandler()],
        config=[
            IfHandler.Config({'FLAG'})
        ]
    )
    assert result == {'key': 'value'}

    result = check_load(
        '!if(FLAG) [item]',
        field=ListField(StringField()),
        tag_handlers=[IfHandler()],
        config=[
            IfHandler.Config({'FLAG'})
        ]
    )

    assert result == ['item']
