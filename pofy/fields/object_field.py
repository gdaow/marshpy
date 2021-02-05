"""Object field class & utilities."""
from gettext import gettext as _
from inspect import isclass
from typing import Any
from typing import Dict
from typing import Optional
from typing import Set
from typing import Type
from typing import cast

from pofy.core.constants import UNDEFINED
from pofy.core.errors import ErrorCode
from pofy.core.interfaces import IBaseField
from pofy.core.interfaces import ILoadingContext
from pofy.core.validation import ValidateCallback
from pofy.core.validation import ValidationContext
from pofy.fields.base_field import BaseField
from pofy.fields.string_field import StringField


_TYPE_FORMAT_MSG = _("""\
Type tag should be in the form !type:path.to.Type, got {}""")


class ObjectField(BaseField):
    """Object YAML object field."""

    def __init__(
        self,
        object_class: Type[Any] = object,
        required: bool = False,
        validate: Optional[ValidateCallback] = None,
    ):
        """Initialize object field.

        Arg:
            required: See BaseField constructor.
            validate: See BaseField constructor.
            object_class: The class of the object to create.

        """
        super().__init__(required=required, validate=validate)
        assert isclass(object_class), \
            _('object_class must be a type')
        self._object_class = object_class

    def _load(self, context: ILoadingContext) -> Any:
        if not context.expect_mapping():
            return UNDEFINED

        object_class = self._resolve_type(context)
        if object_class is None:
            return UNDEFINED

        return _load(object_class, context)

    def _resolve_type(self, context: ILoadingContext) -> Optional[Type[Any]]:
        node = context.current_node()
        tag = str(node.tag)
        if not tag.startswith('!type'):
            return self._object_class

        if ':' not in tag:
            context.error(
                ErrorCode.BAD_TYPE_TAG_FORMAT,
                _TYPE_FORMAT_MSG, tag
            )
            return None

        full_name = tag.split(':')
        if len(full_name) != 2:
            context.error(
                ErrorCode.BAD_TYPE_TAG_FORMAT,
                _TYPE_FORMAT_MSG, tag
            )
            return None

        full_name_str = full_name[1]
        full_name = full_name_str.split('.')

        if len(full_name) < 2:
            context.error(
                ErrorCode.BAD_TYPE_TAG_FORMAT,
                _TYPE_FORMAT_MSG, tag
            )
            return None

        module_name = '.'.join(full_name[:-1])
        type_name = full_name[-1]
        return _get_type(module_name, type_name, context)


def _get_type(
    module_name: str,
    type_name: str,
    context: ILoadingContext
) -> Optional[Type[Any]]:
    full_name = r'{}.{}'.format(module_name, type_name)
    try:
        module = __import__(module_name, fromlist=type_name)
    except ModuleNotFoundError:
        context.error(
            ErrorCode.TYPE_RESOLVE_ERROR,
            _('Can\'t find python module for type {}'), full_name
        )
        return None

    if not hasattr(module, type_name):
        context.error(
            ErrorCode.TYPE_RESOLVE_ERROR,
            _('Can\'t find python type {}'), full_name
        )
        return None

    resolved_type = getattr(module, type_name)

    if not isclass(resolved_type):
        context.error(
            ErrorCode.TYPE_RESOLVE_ERROR,
            _('Python type {} is not a class'), full_name
        )
        return None

    return cast(Type[Any], resolved_type)


def _load(object_class: Type[Any], context: ILoadingContext) -> Any:
    fields = _get_fields(object_class, context)

    if len(fields) == 0:
        context.error(
            ErrorCode.SCHEMA_ERROR,
            _('No Schema class found for type {}, check that your schema is '
              'correctly configured.'),
            object_class.__name__
        )
        return UNDEFINED

    result, set_fields = _load_object(object_class, fields, context)
    if _validate_object(result, fields, set_fields, context):
        _post_load(result, context)
        return result

    return UNDEFINED


def _load_object(
    object_class: Type[Any],
    fields: Dict[str, IBaseField],
    context: ILoadingContext
) -> Any:
    node = context.current_node()
    result = object_class()
    set_fields = set()

    for name_node, value_node in node.value:
        field_name = context.load(StringField(), name_node)
        if field_name is UNDEFINED:
            continue

        field_name = name_node.value
        set_fields.add(field_name)
        if field_name not in fields:
            context.error(
                ErrorCode.FIELD_NOT_DECLARED,
                _('Field {} is not declared.'), field_name
            )
            continue

        field = fields[field_name]
        field_value = context.load(field, value_node)
        if field_value is UNDEFINED:
            continue

        setattr(result, field_name, field_value)

    return (result, set_fields)


def _validate_object(
    obj: Any,
    fields: Dict[str, IBaseField],
    set_fields: Set[str],
    context: ILoadingContext
) -> bool:
    valid_object = True
    for name, field in fields.items():
        if field.required and name not in set_fields:
            valid_object = False
            context.error(
                ErrorCode.MISSING_REQUIRED_FIELD,
                _('Missing required field {}'), name
            )

    hook = context.get_hook(obj, 'validate')

    if hook is not None:
        validation_context = ValidationContext(context)
        hook(validation_context)
        valid_object = valid_object and not validation_context.has_error()

    return valid_object


def _post_load(obj: Any, context: ILoadingContext) -> Any:
    hook = context.get_hook(obj, 'post_load')

    if hook is not None:
        hook()


def _get_fields(cls: Type[Any], context: ILoadingContext) \
        -> Dict[str, IBaseField]:
    fields = {}

    for parent in cls.__bases__:
        parent_fields = _get_fields(parent, context)
        fields.update(parent_fields)

    fields.update(context.get_fields(cls))

    return fields
