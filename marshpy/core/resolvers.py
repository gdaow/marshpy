"""Custom resolvers"""
from typing import Any, Type, get_type_hints, get_args, get_origin

from marshpy.fields.base_field import IBaseField
from marshpy.fields.object_field import ObjectField
from marshpy.fields.bool_field import BoolField
from marshpy.fields.dict_field import DictField
from marshpy.fields.float_field import FloatField
from marshpy.fields.int_field import IntField
from marshpy.fields.list_field import ListField
from marshpy.fields.string_field import StringField


_LITERAL_FIELD_MAPPINGS = {
    str: StringField,
    int: IntField,
    bool: BoolField,
    float: FloatField
}

_CONTAINER_FIELD_MAPPING = {
    dict: DictField,
    list: ListField
}

def annotation_fields_resolver(obj: Any) -> dict[str, IBaseField]:
    result = {}
    annotations = obj.__annotations__
    for member in dir(obj):
        if member not in annotations:
            continue

        member_annotation = annotations[member]

        result[member] = _build_field(member_annotation)

    return result


def _build_field(field_type: Type[Any]):
    if field_type in _LITERAL_FIELD_MAPPINGS:
        return _LITERAL_FIELD_MAPPINGS[field_type]()

    origin_type = get_origin(field_type)
    if origin_type in _CONTAINER_FIELD_MAPPING:
        type_args = get_args(field_type)
        assert len(type_args) == 1
        nested_field = _build_field(type_args[0])
        return _CONTAINER_FIELD_MAPPING[origin_type](nested_field)

    return ObjectField(field_type)


ANNOTATION_RESOLVER_CONFIG = ObjectField.Config(
    fields_resolver=annotation_fields_resolver
)
