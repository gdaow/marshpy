"""Custom resolvers test."""
from marshpy import ANNOTATION_RESOLVER_CONFIG, load


class _AnnotatedType:
    list_field: list[str] = []
    dict_field: dict[str, str] = {}


def test_annotation_resolver() -> None:
    yaml_string = '''
    list_field:
      - item_1
      - item_2
    dict_field:
      key_1: item_1
      key_2: item_2
    '''

    result = load(yaml_string, _AnnotatedType, config=[ANNOTATION_RESOLVER_CONFIG])

    assert isinstance(result, _AnnotatedType)
    assert result.list_field == ['item_1', 'item_2']
    assert result.dict_field == {'key_1': 'item_1', 'key_2': 'item_2'}
