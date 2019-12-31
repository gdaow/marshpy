"""Pyyo deserializing function."""

from gettext import gettext as _
from inspect import getmembers
from inspect import isclass
from io import StringIO
from typing import IO
from typing import Type
from typing import Union

from yaml import compose
from yaml import MappingNode
from yaml import Node

from .errors import parse_error
from .fields.base_field import BaseField


def load(object_class: Type, source: Union[str, IO[str], Node]) -> object:
    """Deserialize a YAML document into an object."""
    node = _load_yaml(source)
    fields = dict(_get_fields(object_class))

    if not isinstance(node, MappingNode):
        parse_error(node, _('Expected a mapping.'))

    result = object_class()
    for name_node, value_node in node.value:
        field_name = name_node.value
        if field_name not in fields:
            parse_error(name_node, _('Unknown field {}'), field_name)

        field = fields[field_name]
        field_value = field.deserialize(value_node)
        setattr(result, field_name, field_value)

    return result


def _get_fields(cls):
    def _is_meta_class(member):
        return isclass(member) and member.__name__ == 'Meta'

    def _is_field(member):
        return isinstance(member, BaseField)

    for __, metaclass in getmembers(cls, _is_meta_class):
        for name, field in getmembers(metaclass, _is_field):
            yield (name, field)


def _load_yaml(source):
    if isinstance(source, Node):
        return source

    if source is str:
        return compose(StringIO(source))

    return compose(source)