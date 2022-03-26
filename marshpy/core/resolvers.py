"""Custom resolvers"""
from typing import Any, Type, get_args, get_origin, get_type_hints

from marshpy.fields.base_field import IBaseField
from marshpy.fields.bool_field import BoolField
from marshpy.fields.dict_field import DictField
from marshpy.fields.float_field import FloatField
from marshpy.fields.int_field import IntField
from marshpy.fields.list_field import ListField
from marshpy.fields.object_field import ObjectField
from marshpy.fields.string_field import StringField

_LITERAL_FIELD_MAPPINGS = {
    str: StringField,
    int: IntField,
    bool: BoolField,
    float: FloatField,
}


def annotation_fields_resolver(obj: Any) -> dict[str, IBaseField]:
    """Fields resolver using type hints to get object field."""
    result = {}
    for name, annotation in get_type_hints(obj).items():
        result[name] = _build_field(annotation)

    return result


def _build_field(field_type: Type[Any]):
    if field_type in _LITERAL_FIELD_MAPPINGS:
        return _LITERAL_FIELD_MAPPINGS[field_type]()

    origin_type = get_origin(field_type)
    type_args = get_args(field_type)
    if origin_type == list:
        assert len(type_args) == 1
        nested_field = _build_field(type_args[0])
        return ListField(nested_field)

    if origin_type == dict:
        assert len(type_args) == 2
        assert type_args[0] == str
        nested_field = _build_field(type_args[1])
        return DictField(nested_field)

    return ObjectField(field_type)


ANNOTATION_RESOLVER_CONFIG = ObjectField.Config(
    fields_resolver=annotation_fields_resolver
)
