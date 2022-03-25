"""Custom resolvers test."""
from marshpy import ANNOTATION_RESOLVER_CONFIG, ObjectField, load


class _AnnotatedType:
    test_field: list[str] = []


def test_annotation_resolver() -> None:
    yaml_string = '''
    test_field:
      - item_1
      - item_2
    '''

    result = load(yaml_string, _AnnotatedType, config=[ANNOTATION_RESOLVER_CONFIG])

    assert isinstance(result, _AnnotatedType)
    assert result.test_field == ['item_1', 'item_2']
