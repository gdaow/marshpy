"""Object field class & utilities."""
from gettext import gettext as _
from inspect import isclass
from typing import Any, Callable, Dict, Optional, Set, Type, cast

from marshpy.core.constants import UNDEFINED
from marshpy.core.errors import ErrorCode
from marshpy.core.interfaces import IBaseField, ILoadingContext
from marshpy.core.validation import ValidateCallback, ValidationContext
from marshpy.fields.base_field import BaseField
from marshpy.fields.string_field import StringField

FieldsResolver = Callable[[Any], Dict[str, IBaseField]]
HookResolver = Callable[[Any, str], Optional[Callable[..., None]]]
ObjectFactory = Callable[[str, ILoadingContext], Any]

_TYPE_FORMAT_MSG = _(
    """\
Type tag should be in the form !type:path.to.Type, got {}"""
)


class ObjectField(BaseField):
    """Object YAML object field."""

    class Config:
        """Shared configuration shared by all fields."""

        def __init__(
            self,
            object_factory: Optional[ObjectFactory] = None,
            fields_resolver: Optional[FieldsResolver] = None,
            hook_resolver: Optional[HookResolver] = None,
        ):
            """Initialize the config class."""
            self._object_factory = (
                object_factory
                if object_factory is not None
                else self._default_object_factory
            )
            self._fields_resolver = (
                fields_resolver
                if fields_resolver is not None
                else self._default_fields_resolver
            )
            self._hook_resolver = (
                hook_resolver
                if hook_resolver is not None
                else self._default_hook_resolver
            )

        def create(self, type_name: str, context: ILoadingContext) -> Optional[Any]:
            """Get hook of given name for given object."""
            return self._object_factory(type_name, context)

        def get_fields(self, obj: Any) -> Dict[str, IBaseField]:
            """Get fields for the given object."""
            return self._fields_resolver(obj)

        def get_hook(self, obj: Any, hook_name: str) -> Optional[Callable[..., None]]:
            """Get hook of given name for given object."""
            return self._hook_resolver(obj, hook_name)

        @staticmethod
        def _default_object_factory(
            type_name: str, context: ILoadingContext
        ) -> Optional[Type[Any]]:
            splitted_name = type_name.split(".")

            if len(splitted_name) < 2:
                context.error(
                    ErrorCode.BAD_TYPE_TAG_FORMAT, _TYPE_FORMAT_MSG, type_name
                )
                return None

            module_name = ".".join(splitted_name[:-1])
            class_name = splitted_name[-1]

            try:
                module = __import__(module_name, fromlist=class_name)
            except ModuleNotFoundError:
                context.error(
                    ErrorCode.TYPE_RESOLVE_ERROR,
                    _("Can't find python module for type {}"),
                    type_name,
                )
                return None

            if not hasattr(module, class_name):
                context.error(
                    ErrorCode.TYPE_RESOLVE_ERROR,
                    _("Can't find python type {}"),
                    type_name,
                )
                return None

            resolved_type = getattr(module, class_name)

            if not isclass(resolved_type):
                context.error(
                    ErrorCode.TYPE_RESOLVE_ERROR,
                    _("Python type {} is not a class"),
                    type_name,
                )
                return None

            return resolved_type()

        @staticmethod
        def _default_fields_resolver(obj: Any) -> Dict[str, IBaseField]:
            return _get_class_fields(obj.__class__)

        @staticmethod
        def _default_hook_resolver(
            obj: Any, hook_name: str
        ) -> Optional[Callable[..., None]]:
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
        assert isclass(object_class), _("object_class must be a type")
        self._object_class = object_class

    def _load(self, context: ILoadingContext) -> Any:
        if not context.expect_mapping():
            return UNDEFINED

        config = context.get_config(ObjectField.Config)
        node = context.current_node()
        tag = str(node.tag)
        if tag.startswith("!type"):
            splitted_tag = tag.split(":")
            if len(splitted_tag) != 2:
                context.error(ErrorCode.BAD_TYPE_TAG_FORMAT, _TYPE_FORMAT_MSG, tag)
                return None
            type_name = splitted_tag[1]
            obj = config.create(type_name, context)
        else:
            obj = self._object_class()

        if obj is None:
            return UNDEFINED

        return _load(obj, context, config)


def _load(obj: Any, context: ILoadingContext, config: ObjectField.Config) -> Any:
    fields = config.get_fields(obj)

    node = context.current_node()
    set_fields = set()

    for name_node, value_node in node.value:
        field_name = context.load(StringField(), name_node)
        if field_name is UNDEFINED:
            continue

        field_name = name_node.value
        set_fields.add(field_name)
        if field_name not in fields:
            context.error(
                ErrorCode.FIELD_NOT_DECLARED, _("Field {} is not declared."), field_name
            )
            continue

        field = fields[field_name]
        field_value = context.load(field, value_node)
        if field_value is UNDEFINED:
            continue

        setattr(obj, field_name, field_value)

    if _validate(obj, fields, set_fields, context, config):
        post_load = config.get_hook(obj, "post_load")
        if post_load is not None:
            post_load()

        return obj

    return UNDEFINED


def _get_class_fields(cls: Type[Any]) -> Dict[str, IBaseField]:
    fields = {}

    for parent in cls.__bases__:
        parent_fields = _get_class_fields(parent)
        fields.update(parent_fields)

    if hasattr(cls, "fields"):
        class_fields = getattr(cls, "fields")
        fields.update(class_fields)

    return fields


def _validate(
    obj: Any,
    fields: Dict[str, IBaseField],
    set_fields: Set[str],
    context: ILoadingContext,
    config: ObjectField.Config,
) -> bool:
    valid_object = True
    for name, field in fields.items():
        if field.required and name not in set_fields:
            valid_object = False
            context.error(
                ErrorCode.MISSING_REQUIRED_FIELD, _("Missing required field {}"), name
            )

    hook = config.get_hook(obj, "validate")

    if hook is not None:
        validation_context = ValidationContext(context)
        hook(validation_context)
        valid_object = valid_object and not validation_context.has_error()

    return valid_object
