"""Object field class & utilities."""
from gettext import gettext as _
from inspect import isclass
from typing import Any
from typing import Dict
from typing import Callable
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

FieldsResolver = Callable[[Type[Any]], Dict[str, IBaseField]]
HookResolver = Callable[[Any, str], Optional[Callable[..., None]]]
TypeResolver = Callable[[str, ILoadingContext], Type[Any]]

_TYPE_FORMAT_MSG = _("""\
Type tag should be in the form !type:path.to.Type, got {}""")


class ObjectField(BaseField):
    """Object YAML object field."""

    class Config:
        """Shared configuration shared by all fields."""

        def __init__(
            self,
            type_resolver: Optional[TypeResolver] = None,
            fields_resolver: Optional[FieldsResolver] = None,
            hook_resolver: Optional[HookResolver] = None,
        ):
            """Initialize the config class."""
            self._type_resolver = type_resolver if type_resolver is not None else self._default_type_resolver
            self._fields_resolver = fields_resolver if fields_resolver is not None else self._default_fields_resolver
            self._hook_resolver = hook_resolver if hook_resolver is not None else self._default_hook_resolver

        def get_type(self, type_name: str, context: ILoadingContext) -> Optional[Type[Any]]:
            """Get hook of given name for given object."""
            return self._type_resolver(type_name, context)

        def get_fields(self, obj: Any) -> Dict[str, IBaseField]:
            """Get fields for the given object."""
            return self._fields_resolver(obj)

        def get_hook(self, obj: Any, hook_name: str) -> Optional[Callable[..., None]]:
            """Get hook of given name for given object."""
            return self._hook_resolver(obj, hook_name)

        @staticmethod
        def _default_type_resolver(type_name: str, context: ILoadingContext) -> Optional[Type[Any]]:
            splitted_name = type_name.split('.')

            if len(splitted_name) < 2:
                context.error(ErrorCode.BAD_TYPE_TAG_FORMAT, _TYPE_FORMAT_MSG, type_name)
                return None

            module_name = '.'.join(splitted_name[:-1])
            class_name = splitted_name[-1]

            try:
                module = __import__(module_name, fromlist=class_name)
            except ModuleNotFoundError:
                context.error(ErrorCode.TYPE_RESOLVE_ERROR, _('Can\'t find python module for type {}'), type_name)
                return None

            if not hasattr(module, class_name):
                context.error(ErrorCode.TYPE_RESOLVE_ERROR, _('Can\'t find python type {}'), type_name)
                return None

            resolved_type = getattr(module, class_name)

            if not isclass(resolved_type):
                context.error(ErrorCode.TYPE_RESOLVE_ERROR, _('Python type {} is not a class'), type_name)
                return None

            return cast(Type[Any], resolved_type)

        @staticmethod
        def _default_fields_resolver(object_class: Type[Any]) -> Dict[str, IBaseField]:
            if not hasattr(object_class, 'fields'):
                return {}

            schema = getattr(object_class, 'fields')
            return cast(Dict[str, IBaseField], schema)

        @staticmethod
        def _default_hook_resolver(obj: Any, hook_name: str) -> Optional[Callable[..., None]]:
            if not hasattr(obj, hook_name):
                return None

            hook = getattr(obj, hook_name)
            return cast(Callable[..., Any], hook)

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
        assert isclass(object_class), _('object_class must be a type')
        self._object_class = object_class

    def _load(self, context: ILoadingContext) -> Any:
        if not context.expect_mapping():
            return UNDEFINED

        config = context.get_config(ObjectField.Config)
        node = context.current_node()
        tag = str(node.tag)
        if tag.startswith('!type'):
            splitted_tag = tag.split(':')
            if len(splitted_tag) != 2:
                context.error(ErrorCode.BAD_TYPE_TAG_FORMAT, _TYPE_FORMAT_MSG, tag)
                return None
            type_name = splitted_tag[1]
            object_class = config.get_type(type_name, context)
        else:
            object_class = self._object_class

        if object_class is None:
            return UNDEFINED

        return _load(object_class, context, config)


def _load(object_class: Type[Any], context: ILoadingContext, config: ObjectField.Config) -> Any:
    fields = _get_fields(object_class, config)

    if len(fields) == 0:
        context.error(
            ErrorCode.SCHEMA_ERROR,
            _('No Schema class found for type {}, check that your schema is '
              'correctly configured.'),
            object_class.__name__
        )
        return UNDEFINED

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

    if _validate(result, fields, set_fields, context, config):
        post_load = config.get_hook(result, 'post_load')
        if post_load is not None:
            post_load()

        return result

    return UNDEFINED


def _get_fields(cls: Type[Any], config: ObjectField.Config) -> Dict[str, IBaseField]:
    fields = {}

    for parent in cls.__bases__:
        parent_fields = _get_fields(parent, config)
        fields.update(parent_fields)

    class_fields = config.get_fields(cls)
    fields.update(class_fields)

    return fields


def _validate(
    obj: Any,
    fields: Dict[str, IBaseField],
    set_fields: Set[str],
    context: ILoadingContext,
    config: ObjectField.Config
) -> bool:
    valid_object = True
    for name, field in fields.items():
        if field.required and name not in set_fields:
            valid_object = False
            context.error(
                ErrorCode.MISSING_REQUIRED_FIELD,
                _('Missing required field {}'), name
            )

    hook = config.get_hook(obj, 'validate')

    if hook is not None:
        validation_context = ValidationContext(context)
        hook(validation_context)
        valid_object = valid_object and not validation_context.has_error()

    return valid_object
