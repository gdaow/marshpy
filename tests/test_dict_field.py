"""List field tests."""
from pyyo import DictField
from pyyo import StringField
from pyyo import YamlObject

class _Test(YamlObject):
    string_dict = DictField(StringField())

def test_int():
    """Test list field deserialization works."""
    test = _Test((
        'string_dict:\n' +
        '  key_1: value_1\n' +
        '  key_2: value_2'
    ))
    assert test.string_dict == {'key_1': 'value_1', 'key_2': 'value_2'}
